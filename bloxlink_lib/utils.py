from typing import Callable, Iterable

def find[T](predicate: Callable, iterable: Iterable[T]) -> T | None:
    """Finds the first element in an iterable that matches the predicate."""

    for element in iterable:
        try:
            iter(element)

            if isinstance(element, str):
                raise TypeError

        except TypeError:
            if predicate(element):
                return element
        else:
            if predicate(*element):
                return element

    return None
