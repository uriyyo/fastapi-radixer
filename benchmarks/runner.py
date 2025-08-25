import time
from dataclasses import dataclass
from functools import partial
from typing import Callable, Any, Awaitable

from fastapi import FastAPI
from starlette.types import ASGIApp

from .apps import get_regular_app, get_radixer_app, get_radixer_fast_app
from .routes import run_cases, BenchmarkFunc
from .cases import init_cases
from .dump import show_results


@dataclass
class BenchmarkResult:
    group: str
    case: str
    elapsed: int


async def run_benchmark[**P, R](
    results: list[BenchmarkResult],
    group: str,
    case: str,
    func: Callable[P, Any],
    /,
    *args: P.args,
    **kwargs: P.kwargs,
) -> R:
    start = time.perf_counter_ns()
    result = await func(*args, **kwargs)
    elapsed = time.perf_counter_ns() - start

    results.append(
        BenchmarkResult(
            group=group,
            case=case,
            elapsed=elapsed,
        ),
    )

    return result


def benchmark_factory(
    results: list[BenchmarkResult],
    group: str,
    app: ASGIApp,
) -> Callable[[BenchmarkFunc], Awaitable[Any]]:
    async def _benchmark(case: BenchmarkFunc, case_name: str | None = None) -> Any:
        case_name = case_name or case.__name__.replace("_", "-")

        return await case(app, partial(run_benchmark, results, group, case_name))

    return _benchmark


async def run_app(
    group: str,
    app: FastAPI,
    *,
    cycles: int | None = None,
    iterations: int | None = None,
) -> list[BenchmarkResult]:
    if iterations is None:
        iterations = 100
    if cycles is None:
        cycles = 10

    results: list[BenchmarkResult] = []

    for _ in range(cycles):
        for _ in range(iterations):
            await run_cases(benchmark_factory(results, group, app.router))

    return results


async def run_benchmarks() -> None:
    init_cases()

    regular_app = get_regular_app()
    radixer_app = get_radixer_app()
    radixer_fast_app = get_radixer_fast_app()

    # warm up
    await run_app("regular", regular_app, iterations=10, cycles=1)
    await run_app("radixer", radixer_app, iterations=10, cycles=1)
    await run_app("radixer-fast", radixer_fast_app, iterations=10, cycles=1)

    regular_results = await run_app("regular", regular_app)
    radixer_results = await run_app("radixer", radixer_app)
    radixer_fast_results = await run_app("radixer-fast", radixer_fast_app)

    show_results(regular_results, radixer_results, radixer_fast_results)


if __name__ == "__main__":
    try:
        import uvloop as _runner
    except ImportError:
        import asyncio as _runner

    _runner.run(run_benchmarks())
