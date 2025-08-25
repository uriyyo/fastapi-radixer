use pyo3::prelude::*;
use pyo3::{FromPyObject, IntoPyObject, PyAny, PyObject};
use std::collections::HashSet;
use std::fmt::Display;

macro_rules! impl_string_key_from_pyobject {
    ($type:ty, $($key:literal => $variant:expr),+ $(,)?) => {
        impl FromPyObject<'_> for $type {
            fn extract_bound(ob: &Bound<'_, PyAny>) -> PyResult<Self> {
                let value: &str = ob.extract()?;
                match value {
                    $($key => Ok($variant),)+
                    _ => Err(pyo3::exceptions::PyValueError::new_err(format!(
                        "Invalid {}: {}",
                        stringify!($type),
                        value
                    ))),
                }
            }
        }
    };
}

pub type Methods = HashSet<String>;

#[derive(Clone, Debug)]
pub enum ParamParseResult {
    UUID(uuid::Uuid),
    Int(i64),
    Float(f64),
    Str(String),
    Path(String),
}

impl<'py> IntoPyObject<'py> for ParamParseResult {
    type Target = PyAny;
    type Output = Bound<'py, Self::Target>;
    type Error = PyErr;

    fn into_pyobject(self, py: Python<'py>) -> Result<Self::Output, Self::Error> {
        match self {
            ParamParseResult::UUID(uuid) => {
                // Optimize: Return string representation directly instead of creating UUID object
                Ok(uuid.to_string().into_pyobject(py)?.into_any())
            }
            ParamParseResult::Int(int) => Ok(int.into_pyobject(py)?.into_any()),
            ParamParseResult::Float(float) => Ok(float.into_pyobject(py)?.into_any()),
            ParamParseResult::Str(string) => Ok(string.into_pyobject(py)?.into_any()),
            ParamParseResult::Path(string) => Ok(string.into_pyobject(py)?.into_any()),
        }
    }
}

#[derive(Copy, Clone, Debug, PartialEq, Eq, PartialOrd, Ord)]
pub enum ParamType {
    UUID,
    Int,
    Float,
    Str,
    Path,
}

impl Display for ParamType {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        let s = match self {
            ParamType::UUID => "uuid",
            ParamType::Int => "int",
            ParamType::Float => "float",
            ParamType::Str => "str",
            ParamType::Path => "path",
        };
        write!(f, "{}", s)
    }
}

impl ParamType {
    pub fn parse(&self, value: &str) -> Option<ParamParseResult> {
        match self {
            ParamType::UUID => uuid::Uuid::parse_str(value)
                .map(ParamParseResult::UUID)
                .ok(),
            ParamType::Int => value.parse::<i64>().map(ParamParseResult::Int).ok(),
            ParamType::Float => value.parse::<f64>().map(ParamParseResult::Float).ok(),
            ParamType::Str => {
                if value.contains('/') {
                    None
                } else {
                    Some(ParamParseResult::Str(value.to_owned()))
                }
            }
            ParamType::Path => Some(ParamParseResult::Path(value.to_owned())),
        }
    }
}

impl_string_key_from_pyobject!(ParamType,
    "uuid" => ParamType::UUID,
    "int" => ParamType::Int,
    "float" => ParamType::Float,
    "str" => ParamType::Str,
    "path" => ParamType::Path,
);

#[derive(Clone, Debug, FromPyObject)]
pub enum PathPart {
    #[pyo3(from_item_all)]
    Static { path: String },
    #[pyo3(from_item_all)]
    Param {
        name: String,
        #[pyo3(item("type"))]
        param_type: ParamType,
    },
}

#[derive(Clone, Debug)]
pub enum StaticRouteKey {
    Static,
}

impl_string_key_from_pyobject!(StaticRouteKey,
    "static" => StaticRouteKey::Static,
);

#[derive(FromPyObject, Debug)]
#[pyo3(from_item_all)]
pub struct StaticRouteDecl {
    pub methods: Methods,
    pub path: String,
    pub route: PyObject,
    pub key: StaticRouteKey,
}

#[derive(Clone, Debug)]
pub enum ParamRouteKey {
    Param,
}

impl_string_key_from_pyobject!(ParamRouteKey,
    "param" => ParamRouteKey::Param,
);

#[derive(FromPyObject, Debug)]
#[pyo3(from_item_all)]
pub struct ParamRouteDecl {
    pub methods: Methods,
    pub path: String,
    pub parts: Vec<PathPart>,
    pub params: Vec<String>,
    pub route: PyObject,
    pub key: ParamRouteKey,
}

#[derive(FromPyObject, Debug)]
pub enum RouteDecl {
    Param(ParamRouteDecl),
    Static(StaticRouteDecl),
}

#[derive(IntoPyObject, Debug)]
pub struct LookupResult {
    pub route: PyObject,
    pub args: Vec<ParamParseResult>,
}
