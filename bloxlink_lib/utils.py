from typing import Callable

async def async_filter[T](func: Callable, iterable: list[T]):
    """Filter an iterable using an async function."""

    return [i for i in iterable if await func(i)]
