from typing import Any, Protocol

from starlette.routing import Route

from .types import RouteDecl


class RadixerRoutingTable(Protocol):
    def add_route(self, route: RouteDecl) -> None:
        pass

    def lookup(self, method: str, path: str) -> tuple[Route, dict[str, Any]] | None:
        pass

    def prepare(self) -> None:
        pass


__all__ = [
    "RadixerRoutingTable",
]
