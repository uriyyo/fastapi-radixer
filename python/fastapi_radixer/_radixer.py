from typing import TYPE_CHECKING, Any, cast

from fastapi import APIRouter, FastAPI
from starlette._utils import get_route_path
from starlette.routing import BaseRoute, Route
from starlette.types import Receive, Scope, Send

from ._base import RadixerRoutingTable
from ._routing_table import RoutingTable
from .parser import parse_route, prepare_path
from .types import Method


class Radixer(APIRouter):
    routing_table: RadixerRoutingTable
    fallback: bool

    if not TYPE_CHECKING:

        def __init__(
            self,
            *args: Any,
            routing_table: RadixerRoutingTable | None = None,
            fallback: bool = True,
            **kwargs: Any,
        ) -> None:
            super().__init__(*args, **kwargs)
            self.routing_table = routing_table or RoutingTable()
            self.fallback = fallback

        def add_api_route(self, *args: Any, **kwargs: Any) -> None:
            super().add_api_route(*args, **kwargs)
            self.try_add_route(self.routes[-1])

        def add_route(self, *args: Any, **kwargs: Any) -> None:
            super().add_route(*args, **kwargs)
            self.try_add_route(self.routes[-1])

    def try_add_route(self, route: BaseRoute) -> None:
        if not isinstance(route, Route):
            return

        if decl := parse_route(route):
            self.routing_table.add_route(decl)

    def add_routes(self, routes: list[BaseRoute]) -> None:
        for route in routes:
            self.try_add_route(route)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await super().__call__(scope, receive, send)
            return

        self.routing_table.prepare()

        scope.setdefault("router", self)

        path = prepare_path(get_route_path(scope))
        method = cast(Method, scope["method"])

        res = self.routing_table.lookup(method, path)

        if res is None:
            if not self.fallback:
                await self.not_found(scope, receive, send)
                return

            await super().__call__(scope, receive, send)
            return

        route, params = res

        scope.update(
            {
                "route": route,
                "endpoint": route.endpoint,
                "path_params": scope.get("path_params", {}) | params,
            },
        )

        await route.handle(scope, receive, send)

        return


def init_app(
    app: FastAPI,
    radixer: Radixer | None = None,
) -> None:
    radixer = radixer or Radixer()

    # there is no way to change default router in FastAPI, so we copy all attributes
    # from app.router to radixer and then add all existing routes to radixer
    radixer.__dict__.update(app.router.__dict__)

    for route in app.router.routes:
        radixer.try_add_route(route)

    app.router = radixer


__all__ = [
    "Radixer",
    "init_app",
]
