from asyncio import gather
from functools import partial
from typing import Iterator, Callable, Any, Awaitable

from fastapi import APIRouter
from starlette.types import ASGIApp, Message

from fastapi_radixer._base import RadixerRoutingTable

routes: list[tuple[str, str, str]] = []


def add_route(method: str, path: str, params: dict[str, Any] | None = None) -> None:
    routes.append((method, path, path.format(**(params or {}))))


def get_cases() -> Iterator[tuple[str, str]]:
    for method, _, case in routes:
        yield method, case


async def _endpoint() -> None:
    pass


def create_router() -> APIRouter:
    router = APIRouter()

    for method, path, _ in routes:
        router.add_api_route(
            path=path,
            endpoint=_endpoint,
            methods=[method],
        )

    return router


type BenchmarkFunc = Callable[[ASGIApp, Any], Awaitable[None]]


def is_success_msg(msg: Message) -> bool:
    match msg:
        case {"type": "http.response.start", "status": status} if 200 <= status < 300:
            return True
        case _:
            return False


async def _async_wrapper(func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
    return func(*args, **kwargs)


async def _run_lookup_case(method: str, path: str, app: RadixerRoutingTable, benchmark: Any) -> None:
    route = await benchmark(_async_wrapper, app.lookup, method, path.strip("/"))
    assert route is not None, f"{method}:{path} - {route}"


async def _run_case(method: str, path: str, app: ASGIApp, benchmark: Any) -> None:
    messages = []

    async def _recv():
        return {
            "type": "http.request",
            "body": b"{}",
            "more_body": False,
        }

    async def _send(message: dict) -> None:
        messages.append(message)

    await benchmark(
        app,
        {
            "type": "http",
            "method": method,
            "path": path,
            "headers": [],
            "query_string": b"",
        },
        _recv,
        _send,
    )

    assert any(is_success_msg(m) for m in messages), f"{method}:{path} - {messages}"


async def run_cases(
    run_benchmark: Callable[..., Awaitable[None]],
    suite: str = "routing",
) -> None:
    if suite == "routing":
        func = _run_case
    else:
        func = _run_lookup_case

    await gather(
        *(
            run_benchmark(
                partial(func, method, path),
                path,
            )
            for method, path in get_cases()
        )
    )


__all__ = [
    "get_cases",
    "run_cases",
    "add_route",
    "create_router",
    "BenchmarkFunc",
]
