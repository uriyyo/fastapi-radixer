from collections.abc import Callable, Iterable


def take_while[T](it: Iterable[T], predicate: Callable[[T], bool]) -> Iterable[T]:
    for x in it:
        if predicate(x):
            yield x
        else:
            break


__all__ = [
    "take_while",
]
