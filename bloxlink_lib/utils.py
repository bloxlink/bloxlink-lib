from typing import Callable, Iterable, Awaitable, Type
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

def find[T](predicate: Callable, iterable: Iterable[T]) -> T | None:
    """Finds the first element in an iterable that matches the predicate."""

    for element in iterable:
        if isinstance(element, Iterable) and not isinstance(element, str):
            if predicate(*element):
                return element
        else:
            if predicate(element):
                return element

    return None

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
