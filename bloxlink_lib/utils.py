from typing import Callable, Iterable

def find[T](predicate: Callable, iterable: Iterable[T]) -> T | None:
    """Finds the first element in an iterable that matches the predicate."""

    for element in iterable:
        if predicate(element):
            return element

    return None
