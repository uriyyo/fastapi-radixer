mod fast_routing_table;
mod types;

use pyo3::prelude::*;

#[pymodule]
mod _fast_routing_table {
    #[pymodule_export]
    use crate::fast_routing_table::FastRoutingTable;
}
