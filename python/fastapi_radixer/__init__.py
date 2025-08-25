from typing import Any

from ._radixer import Radixer, init_app
from ._routing_table import RoutingTable

try:
    from ._fast_routing_table import FastRoutingTable
except ImportError:

    class FastRoutingTable:
        def __init__(self, *_: Any, **__: Any) -> None:
            raise ImportError("FastRoutingTable is not available")


__all__ = [
    "FastRoutingTable",
    "Radixer",
    "RoutingTable",
    "init_app",
]
