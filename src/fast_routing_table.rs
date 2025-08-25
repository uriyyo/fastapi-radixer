use crate::types::{Methods, ParamParseResult, ParamRouteDecl, ParamType, PathPart, RouteDecl, StaticRouteDecl};
use pyo3::{pyclass, pymethods, PyObject, PyResult, Python, exceptions::PyRuntimeError};
use rustc_hash::{FxHashMap, FxHashSet};
use std::collections::{BTreeMap, VecDeque};
use std::sync::Arc;
use pyo3::types::PyString;

struct RoutingTrie {
    methods: Methods,
    leafs: Vec<ParamRouteDecl>,

    static_parts: FxHashMap<String, RoutingTrie>,
    param_parts: BTreeMap<ParamType, RoutingTrie>,

    radix_node: Option<(String, Box<RoutingTrie>)>,
}

impl RoutingTrie {
    fn new() -> Self {
        RoutingTrie {
            methods: FxHashSet::with_capacity_and_hasher(4, Default::default()), // Common: GET, POST, PUT, DELETE
            leafs: Vec::new(),
            static_parts: FxHashMap::with_capacity_and_hasher(2, Default::default()), // Most nodes have 1-2 children
            param_parts: BTreeMap::new(),
            radix_node: None,
        }
    }

    fn is_radix(&self) -> bool {
        self.radix_node.is_some()
    }

    fn add_route(&mut self, route: ParamRouteDecl, parts: &[PathPart]) {
        self.methods.extend(route.methods.iter().cloned());

        if parts.is_empty() {
            self.leafs.push(route);
            return;
        }

        let (part, rest) = parts.split_first().unwrap();

        match part {
            PathPart::Static { path, .. } => {
                let child = self
                    .static_parts
                    .entry(path.clone())
                    .or_insert_with(|| RoutingTrie::new());

                child.add_route(route, rest);
            }
            PathPart::Param {
                name: _,
                param_type,
            } => {
                let child = self
                    .param_parts
                    .entry(*param_type)
                    .or_insert_with(|| RoutingTrie::new());

                child.add_route(route, rest);
            }
        }
    }

    fn prepare_trie(&mut self) {
        self.static_parts
            .values_mut()
            .for_each(|child| child.prepare_trie());
        self.param_parts
            .values_mut()
            .for_each(|child| child.prepare_trie());

        if !self.param_parts.is_empty() {
            return;
        }

        if !self.leafs.is_empty() {
            return;
        }

        if self.static_parts.len() != 1 {
            return;
        }

        match self.static_parts.drain().take(1).next() {
            Some((path, trie)) => {
                if trie.is_radix() {
                    let (sub_path, sub_trie) = trie.radix_node.unwrap();

                    let mut combined_path = String::with_capacity(path.len() + sub_path.len() + 1);
                    combined_path.push_str(&path);
                    combined_path.push('/');
                    combined_path.push_str(&sub_path);

                    self.radix_node = Some((combined_path, sub_trie));
                } else {
                    self.radix_node = Some((path, Box::new(trie)));
                }
            }
            None => { /* unreachable */ }
        }

        ()
    }

    fn lookup(&self, method: &str, path: &str) -> Option<(&ParamRouteDecl, Option<VecDeque<ParamParseResult>>)> {
        // Check if we have any methods at all for this subtree
        if !self.methods.contains(method) {
            return None;
        }

        // Handle leaf nodes (end of path)
        if path.is_empty() {
            for leaf in &self.leafs {
                if leaf.methods.contains(method) {
                    return Some((leaf, None));
                }
            }
            return None;
        }

        // Handle radix-compressed paths
        if let Some((single_path, single_trie)) = &self.radix_node {
            if path.starts_with(single_path){
                let remaining_path = &path[single_path.len() + 1..];
                return single_trie.lookup(method, remaining_path);
            }
        }

        // Split path for regular trie traversal
        let (part, rest) = match path.split_once('/') {
            Some((part, rest)) => (part, rest),
            None => (path, ""),
        };

        // Try static routes first (faster)
        if let Some(child) = self.static_parts.get(part) {
            if let Some(res) = child.lookup(method, rest) {
                return Some(res);
            }
        }

        // Try parameter routes
        for (param_type, child) in &self.param_parts {
            let parsed = match param_type.parse(part) {
                Some(parsed) => parsed,
                None => continue,
            };

            if let Some((decl, args)) = child.lookup(method, rest) {
                let mut args = args.unwrap_or_else(|| VecDeque::with_capacity(decl.params.len()));
                args.push_front(parsed);
                return Some((decl, Some(args)));
            }
        }

        None
    }

    pub fn dump(&self, py: Python, tree: &PyObject) -> PyResult<()> {
        if let Some((path, child)) = &self.radix_node {
            let node = tree.call_method1(py, "add", (PyString::new(py, path),))?;
            child.dump(py, &node)?;

            return Ok(());
        }

        for (path, child) in &self.static_parts {
            let node = tree.call_method1(py, "add", (PyString::new(py, path),))?;
            child.dump(py, &node)?;
        }

        for (param_type, child) in &self.param_parts {
            let param = format!("{{{}}}", param_type);
            let node = tree.call_method1(py, "add", (PyString::new(py, &param),))?;
            child.dump(py, &node)?;
        }

        Ok(())
    }
}

#[pyclass]
pub struct FastRoutingTable {
    trie: RoutingTrie,
    static_routes: FxHashMap<String, FxHashMap<String, Arc<StaticRouteDecl>>>,
    prepared: bool,
}

impl FastRoutingTable {
    fn add_static_route(&mut self, route: StaticRouteDecl) {
        let route_rc = Arc::new(route);

        for method in &route_rc.methods {
            self.static_routes
                .entry(route_rc.path.clone())
                .or_insert_with(|| FxHashMap::with_capacity_and_hasher(4, Default::default()))
                .insert(method.clone(), route_rc.clone());
        }
    }

    fn add_param_route(&mut self, route: ParamRouteDecl) {
        let parts = route.parts.clone();
        self.trie.add_route(route, &parts);
    }
}

#[pymethods]
impl FastRoutingTable {
    #[new]
    pub fn new() -> Self {
        FastRoutingTable {
            trie: RoutingTrie::new(),
            static_routes: FxHashMap::with_capacity_and_hasher(16, Default::default()),
            prepared: false,
        }
    }

    pub fn prepare(&mut self) {
        if self.prepared {
            return;
        }

        self.trie.prepare_trie();
        self.prepared = true;
    }

    pub fn add_route(&mut self, route: RouteDecl) -> PyResult<()> {
        if self.prepared {
            return Err(PyRuntimeError::new_err("Cannot add routes after prepare() has been called"));
        }

        match route {
            RouteDecl::Static(static_route) => self.add_static_route(static_route),
            RouteDecl::Param(param_route) => self.add_param_route(param_route),
        }
        Ok(())
    }

    pub fn lookup(
        &self,
        method: &str,
        path: &str,
    ) -> PyResult<Option<(&PyObject, FxHashMap<&str, ParamParseResult>)>> {
        // Fast path for static routes using original nested approach
        if let Some(methods) = self.static_routes.get(path) {
            if let Some(route) = methods.get(method) {
                return Ok(Some((&route.route, FxHashMap::default())));
            }
        }

        // Parameterized routes via trie
        if let Some((decl, args)) = self.trie.lookup(method, path) {
            let params: FxHashMap<&str, ParamParseResult> = match args {
                Some(args) => {
                    decl.params
                        .iter()
                        .map(|s| s.as_str())
                        .zip(args.into_iter())
                        .collect()
                },
                None => FxHashMap::default(),
            };

            return Ok(Some((&decl.route, params)));
        }

        Ok(None)
    }

    pub fn dump(&self, tree: PyObject) -> PyResult<()> {
        Python::with_gil(|py| -> PyResult<()> {
            for path in self.static_routes.keys() {
                tree.call_method1(py, "add", (PyString::new(py, path),))?;
            }

            self.trie.dump(py, &tree)?;

            Ok(())
        })?;

        Ok(())
    }
}
