from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from itertools import chain
from typing import TYPE_CHECKING

from rich.table import Table
from rich.text import Text
from rich import print

if TYPE_CHECKING:
    from .runner import BenchmarkResult


@dataclass
class CaseResult:
    min: float
    max: float
    mean: float
    median: float
    total: float


def _get_mean(times: list[float]) -> float:
    return sum(times) / len(times)


def _get_median(times: list[float]) -> float:
    n = len(times)

    mid = n // 2
    if n % 2 == 1:
        return times[mid]
    else:
        return (times[mid - 1] + times[mid]) / 2


def _min(times: list[float]) -> float:
    return max(times[:20])


def _max(times: list[float]) -> float:
    return min(times[-20:])


def benchmark_results_to_case_result(results: list[BenchmarkResult]) -> CaseResult:
    times = sorted(r.elapsed for r in results)

    return CaseResult(
        min=_min(times),
        max=_max(times),
        mean=_get_mean(times),
        median=_get_median(times),
        total=sum(times),
    )


def show_results(*results: list[BenchmarkResult]) -> None:
    groups = {r.group for result in results for r in result}
    cases = {r.case for result in results for r in result}

    by_case_and_group: dict[tuple[str | None, str], list[BenchmarkResult]] = defaultdict(list)
    for result in results:
        for r in result:
            by_case_and_group[(r.case, r.group)].append(r)
            by_case_and_group[(None, r.group)].append(r)

    grouped: dict[str | None, dict[str, CaseResult]] = defaultdict(dict)
    for (case, group), result in by_case_and_group.items():
        grouped[case][group] = benchmark_results_to_case_result(result)

    for case in chain(sorted(cases), [None]):
        display_results(case, groups, grouped[case])


def _get_relative_text(value: float, best: float) -> Text:
    value = value / 1_000
    best = best / 1_000

    if value == best:
        return Text(f"{value:.2f} (1.00)", style="green")
    else:
        ratio = value / best
        return Text(f"{value:.2f} ({ratio:.2f})", style="red")


def display_results(case: str | None, groups: set[str], results: dict[str, CaseResult]) -> None:
    table = Table(title=f"Results for case: {case or 'all'}")

    table.add_column("Group")
    table.add_column("Min (µs)", justify="right")
    table.add_column("Max (µs)", justify="right")
    table.add_column("Mean (µs)", justify="right")
    table.add_column("Median (µs)", justify="right")
    table.add_column("Total (µs)", justify="right")

    best_min = min((r.min for r in results.values()), default=0)
    best_max = min((r.max for r in results.values()), default=0)
    best_mean = min((r.mean for r in results.values()), default=0)
    best_median = min((r.median for r in results.values()), default=0)
    best_total = min((r.total for r in results.values()), default=0)

    for group in sorted(groups):
        r = results[group]

        table.add_row(
            group,
            _get_relative_text(r.min, best_min),
            _get_relative_text(r.max, best_max),
            _get_relative_text(r.mean, best_mean),
            _get_relative_text(r.median, best_median),
            _get_relative_text(r.total, best_total),
        )

    print(table)
