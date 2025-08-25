from typing import Any, Protocol

from rich.tree import Tree
from starlette.routing import Route

from .types import Method, Path, RouteDecl


class RadixerRoutingTable(Protocol):
    def add_route(self, route: RouteDecl) -> None:
        pass

    def lookup(self, method: Method, path: Path) -> tuple[Route, dict[str, Any]] | None:
        pass

    def prepare(self) -> None:
        pass

    def dump(self, tree: Tree) -> None:
        pass


__all__ = [
    "RadixerRoutingTable",
]
