from typing import Any, Literal, TypedDict

from starlette.routing import Route
from typing_extensions import TypeIs

type Method = Literal[
    "GET",
    "POST",
    "PUT",
    "DELETE",
    "PATCH",
    "HEAD",
    "OPTIONS",
]
type Methods = set[Method]

type Path = str

type ParamType = Literal[
    "int",
    "float",
    "uuid",
    "str",
    "path",
]

type ParsedParams = dict[str, Any]


class BaseRouteDecl(TypedDict):
    route: Route
    methods: set[Method]


class StaticRouteDecl(BaseRouteDecl):
    key: Literal["static"]
    path: Path


class ParamPathPart(TypedDict):
    key: Literal["param"]
    name: str
    type: ParamType


class StaticPathPart(TypedDict):
    key: Literal["static"]
    path: Path


type PathPart = StaticPathPart | ParamPathPart


class ParamRouteDecl(BaseRouteDecl):
    key: Literal["param"]
    path: Path
    parts: list[PathPart]
    params: list[str]


type RouteDecl = StaticRouteDecl | ParamRouteDecl


def is_static_route(route: RouteDecl) -> TypeIs[StaticRouteDecl]:
    return route["key"] == "static"


def is_param_route(route: RouteDecl) -> TypeIs[ParamRouteDecl]:
    return route["key"] == "param"


def is_static_path_part(part: PathPart) -> TypeIs[StaticPathPart]:
    return part["key"] == "static"


def is_param_path_part(part: PathPart) -> TypeIs[ParamPathPart]:
    return part["key"] == "param"


__all__ = [
    "BaseRouteDecl",
    "Method",
    "Methods",
    "ParamPathPart",
    "ParamRouteDecl",
    "ParamType",
    "ParsedParams",
    "Path",
    "PathPart",
    "RouteDecl",
    "StaticPathPart",
    "StaticRouteDecl",
    "is_param_path_part",
    "is_param_route",
    "is_static_path_part",
    "is_static_route",
]
