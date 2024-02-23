from typing import Callable, Iterable, Awaitable, Type, Any, Optional, AsyncIterable, overload, TypeVar, Coroutine, Union
import importlib
import logging
import asyncio
from os import listdir, getenv
from inspect import iscoroutinefunction
from types import ModuleType
import sentry_sdk
from sentry_sdk.integrations.aiohttp import AioHttpIntegration
from .models.base import BaseModel
from .config import CONFIG



# find function from discord.py (https://github.com/Rapptz/discord.py/blob/master/discord/utils.py)
T = TypeVar('T')
_Iter = Union[Iterable[T], AsyncIterable[T]]
Coro = Coroutine[Any, Any, T]

def _find(predicate: Callable[[T], Any], iterable: Iterable[T], /) -> Optional[T]:
    return next((element for element in iterable if predicate(element)), None)


async def _afind(predicate: Callable[[T], Any], iterable: AsyncIterable[T], /) -> Optional[T]:
    async for element in iterable:
        if predicate(element):
            return element

    return None


@overload
def find(predicate: Callable[[T], Any], iterable: AsyncIterable[T], /) -> Coro[Optional[T]]:
    ...


@overload
def find(predicate: Callable[[T], Any], iterable: Iterable[T], /) -> Optional[T]:
    ...


def find(predicate: Callable[[T], Any], iterable: _Iter[T], /) -> Union[Optional[T], Coro[Optional[T]]]:
    r"""A helper to return the first element found in the sequence
    that meets the predicate.

    This is different from :func:`py:filter` due to the fact it stops the moment it finds
    a valid entry.

    Parameters
    -----------
    predicate
        A function that returns a boolean-like result.
    iterable: Union[:class:`collections.abc.Iterable`, :class:`collections.abc.AsyncIterable`]
        The iterable to search through. Using a :class:`collections.abc.AsyncIterable`,
        makes this function return a :term:`coroutine`.
    """

    return (
        _afind(predicate, iterable)  # type: ignore
        if hasattr(iterable, '__aiter__')  # isinstance(iterable, collections.abc.AsyncIterable) is too slow
        else _find(predicate, iterable)  # type: ignore
    )


def load_module(import_name: str) -> ModuleType:
    """Utility function to import python modules.

    Args:
        import_name (str): Name of the module to import
    """

    logging.info(f"Attempting to load module {import_name}")

    try:
        module = importlib.import_module(import_name)

    except (ImportError, ModuleNotFoundError) as e:
        logging.error(f"Failed to import {import_name}: {e}")
        raise

    except Exception as e:
        logging.error(f"Module {import_name} errored: {e}")
        raise

    if hasattr(module, "__setup__"):
        try:
            if iscoroutinefunction(module.__setup__):
                asyncio.run(module.__setup__())
            else:
                module.__setup__()

        except Exception as e:
            logging.error(f"Module {import_name} errored: {e}")
            raise e

    logging.info(f"Loaded module {import_name}")

    return module

def load_modules(*paths: tuple[str], starting_path: str=".") -> list[ModuleType]:
    """Utility function to import python modules.

    Args:
        paths (list[str]): Paths of modules to import
    """

    modules: list[ModuleType] = []

    for directory in paths:
        files = [
            name
            for name in listdir(starting_path + directory.replace(".", "/"))
            if name[:1] != "." and name[:2] != "__" and name != "_DS_Store"
        ]

        for filename in [f.replace(".py", "") for f in files]:
            if filename in ("__main__", "__init__"):
                continue

            module = load_module(f"{directory.replace('/','.')}.{filename}")

            if module:
                modules.append(module)

    return modules

def create_task_log_exception(awaitable: Awaitable) -> asyncio.Task:
    """Creates a task that logs exceptions."""
    # https://stackoverflow.com/questions/30361824/asynchronous-exception-handling-in-python

    async def _log_exception(awaitable):
        try:
            return await awaitable

        except Exception as e: # pylint: disable=broad-except
            logging.exception(e)

    return asyncio.create_task(_log_exception(awaitable))

def get_node_id() -> int:
    """Gets the node ID from the hostname."""

    hostname = getenv("HOSTNAME", "bloxlink-0")

    try:
        node_id = int(hostname.split("-")[-1])
    except ValueError:
        node_id = 0

    return node_id

def get_node_count() -> int:
    """Gets the node count."""

    shards_per_node = CONFIG.SHARDS_PER_NODE
    shard_count = CONFIG.SHARD_COUNT

    return shard_count // shards_per_node

def parse_into[T: BaseModel | dict](data: dict, model: Type[T]) -> T:
    """Parse a dictionary into a dataclass.

    Args:
        data (dict): The dictionary to parse.
        model (Type[T]): The dataclass to parse the dictionary into.

    Returns:
        T: The dataclass instance of the response.
    """

    if issubclass(model, BaseModel):
        # Filter only relevant fields before constructing the pydantic instance
        relevant_fields = {field_name: data.get(field_name, data.get(field.alias)) for field_name, field in model.model_fields.items() if field_name in data or field.alias in data}

        return model(**relevant_fields)

    return model(**data)

def init_sentry():
    """Initialize Sentry."""

    if CONFIG.SENTRY_DSN:
        sentry_sdk.init(
            dsn=CONFIG.SENTRY_DSN,
            integrations=[AioHttpIntegration()],
            enable_tracing=True,
            debug=True,
            attach_stacktrace=True
        )
