use crate::types::{
    Methods, ParamParseResult, ParamRouteDecl, ParamType, RouteDecl, StaticRouteDecl,
};
use pyo3::{pyclass, pymethods, PyObject, PyResult, Python};
use std::collections::{BTreeMap, HashMap};
use pyo3::types::PyString;

struct RoutingTrie {
    methods: Methods,
    leafs: Vec<ParamRouteDecl>,

    static_parts: HashMap<String, RoutingTrie>,
    param_parts: BTreeMap<ParamType, RoutingTrie>,

    radix_node: Option<(String, Box<RoutingTrie>)>,
}

impl RoutingTrie {
    fn new() -> Self {
        RoutingTrie {
            methods: Methods::new(),
            leafs: Vec::new(),
            static_parts: HashMap::new(),
            param_parts: BTreeMap::new(),
            radix_node: None,
        }
    }

    fn is_radix(&self) -> bool {
        self.radix_node.is_some()
    }

    fn add_route(&mut self, route: ParamRouteDecl, parts: Vec<crate::types::PathPart>) {
        self.methods.extend(route.methods.clone());

        if parts.is_empty() {
            self.leafs.push(route);
            return;
        }

        let (part, rest) = parts.split_first().unwrap();

        match part {
            crate::types::PathPart::Static { path, .. } => {
                let child = self
                    .static_parts
                    .entry(path.clone())
                    .or_insert_with(|| RoutingTrie::new());

                child.add_route(route, rest.to_vec());
            }
            crate::types::PathPart::Param {
                name: _,
                param_type,
            } => {
                let child = self
                    .param_parts
                    .entry(param_type.clone())
                    .or_insert_with(|| RoutingTrie::new());

                child.add_route(route, rest.to_vec());
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

    fn lookup(&self, method: &str, path: &str) -> Option<(&ParamRouteDecl, Vec<ParamParseResult>)> {
        if !self.methods.contains(method) {
            return None;
        }

        if path.is_empty() {
            for leaf in &self.leafs {
                if leaf.methods.contains(method) {
                    return Some((leaf, Vec::new()));
                }
            }
        }

        if let Some((single_path, single_trie)) = &self.radix_node {
            if path.starts_with(single_path) {
                let remaining_path = &path[single_path.len() + 1..];
                return single_trie.lookup(method, remaining_path);
            }
        }

        let (part, rest) = match path.find("/") {
            Some(index) => (&path[..index], &path[index + 1..]),
            None => (path, ""),
        };

        if let Some(child) = self.static_parts.get(part) {
            if let Some(res) = child.lookup(method, rest) {
                return Some(res);
            }
        }

        for (param_type, child) in &self.param_parts {
            let parsed = match param_type.parse(part) {
                Some(parsed) => parsed,
                None => continue,
            };

            if let Some((decl, args)) = child.lookup(method, rest) {
                let mut new_args = args.clone();
                new_args.insert(0, parsed);

                return Some((decl, new_args));
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
    static_routes: HashMap<String, Vec<(Methods, StaticRouteDecl)>>,
    prepared: bool,
}

impl FastRoutingTable {
    fn add_static_route(&mut self, route: StaticRouteDecl) {
        let entry = self
            .static_routes
            .entry(route.path.clone())
            .or_insert_with(Vec::new);

        entry.push((route.methods.clone(), route));
    }

    fn add_param_route(&mut self, route: ParamRouteDecl) {
        let parts = route.parts.clone();
        self.trie.add_route(route, parts);
    }
}

#[pymethods]
impl FastRoutingTable {
    #[new]
    pub fn new() -> Self {
        FastRoutingTable {
            trie: RoutingTrie::new(),
            static_routes: HashMap::new(),
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

    pub fn add_route(&mut self, route: RouteDecl) {
        if self.prepared {
            panic!("Cannot add routes after prepare() has been called");
        }

        match route {
            RouteDecl::Static(static_route) => self.add_static_route(static_route),
            RouteDecl::Param(param_route) => self.add_param_route(param_route),
        }
    }

    pub fn lookup(
        &self,
        method: &str,
        path: &str,
    ) -> PyResult<Option<(&PyObject, HashMap<&String, ParamParseResult>)>> {
        if let Some(static_routes) = self.static_routes.get(path) {
            for (_, route) in static_routes {
                if route.methods.contains(method) {
                    return Ok(Some((&route.route, HashMap::new())));
                }
            }
        }

        if let Some((decl, args)) = self.trie.lookup(method, path) {
            let params = decl.params.iter().zip(args.into_iter()).collect();

            return Ok(Some((&decl.route, params)));
        }

        Ok(None)
    }

    pub fn dump(&self, tree: PyObject) -> PyResult<()> {
        Python::with_gil(|py| -> PyResult<()> {
            for (path, _) in &self.static_routes {
                tree.call_method1(py, "add", (PyString::new(py, path),))?;
            }

            self.trie.dump(py, &tree)?;

            Ok(())
        })?;

        Ok(())
    }
}
