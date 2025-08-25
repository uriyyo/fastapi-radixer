from fastapi import FastAPI

from fastapi_radixer import Radixer, init_app, RoutingTable, FastRoutingTable
from .routes import create_router


def get_regular_app() -> FastAPI:
    app = FastAPI()
    app.include_router(create_router())

    return app


def get_radixer_app() -> FastAPI:
    app = get_regular_app()

    radixer = Radixer(routing_table=RoutingTable())
    radixer.fallback = False

    init_app(app, radixer=radixer)

    return app


def get_radixer_fast_app() -> FastAPI:
    app = get_regular_app()

    radixer = Radixer(routing_table=FastRoutingTable())
    radixer.fallback = True

    init_app(app, radixer=radixer)

    return app


__all__ = [
    "get_regular_app",
    "get_radixer_app",
    "get_radixer_fast_app",
]
