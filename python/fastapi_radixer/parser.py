import math
import uuid
from collections.abc import Callable, Iterator
from typing import Any, cast

from starlette.convertors import (
    Convertor,
    FloatConvertor,
    IntegerConvertor,
    PathConvertor,
    StringConvertor,
    UUIDConvertor,
)
from starlette.routing import Route

from .types import (
    Method,
    Methods,
    ParamPathPart,
    ParamRouteDecl,
    ParamType,
    PathPart,
    RouteDecl,
    StaticPathPart,
    StaticRouteDecl,
    is_param_path_part,
)


def prepare_path(path: str) -> str:
    return path.strip("/")


_PARAM_TYPE_PRIORITY: dict[ParamType, int] = {
    "uuid": 0,
    "int": 1,
    "float": 2,
    "str": 3,
    "path": 4,
}

_PARAM_VALIDATORS: dict[ParamType, Callable[[str], Any]] = {
    "uuid": uuid.UUID,
    "int": int,
    "float": float,
    "str": lambda v: "/" not in v,
    "path": lambda: True,
}


def param_priority_key(param_type: ParamType) -> float:
    return _PARAM_TYPE_PRIORITY.get(param_type, math.inf)


def parse_param_part(param_type: ParamType, value: str) -> tuple[bool, Any]:
    try:
        val = _PARAM_VALIDATORS[param_type](value)
    except (ValueError, TypeError, AssertionError):
        return False, None
    else:
        return True, val


def convertor_to_param_type(convertor: Convertor) -> ParamType | None:
    match convertor:
        case StringConvertor():
            return "str"
        case PathConvertor():
            return "path"
        case IntegerConvertor():
            return "int"
        case FloatConvertor():
            return "float"
        case UUIDConvertor():
            return "uuid"
        case _:
            return None


def path_parts_iter(
    path: str,
    params: dict[str, ParamType],
) -> Iterator[PathPart]:
    for part in path.split("/"):
        if part.startswith("{") and part.endswith("}"):
            param_name = part[1:-1]
            param_type = params.get(param_name)

            if param_type is None:
                continue

            yield ParamPathPart(
                key="param",
                name=param_name,
                type=param_type,
            )
        else:
            yield StaticPathPart(
                key="static",
                path=part,
            )


def parse_route(route: Route) -> RouteDecl | None:
    path = prepare_path(route.path_format)
    methods: Methods = {cast(Method, m.upper()) for m in route.methods or ()}
    params = {key: convertor_to_param_type(value) for key, value in route.param_convertors.items()}

    if any(v is None for v in params.values()):
        return None

    if not params:
        return StaticRouteDecl(
            key="static",
            route=route,
            methods=methods,
            path=path,
        )

    params = cast(dict[str, ParamType], params)
    parts = [*path_parts_iter(path, params)]

    return ParamRouteDecl(
        key="param",
        route=route,
        methods=methods,
        path=path,
        parts=parts,
        params=[p["name"] for p in parts if is_param_path_part(p)],
    )


__all__ = [
    "param_priority_key",
    "parse_param_part",
    "parse_route",
    "prepare_path",
]
