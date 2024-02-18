from typing import Callable, Iterable, Awaitable
import importlib
import logging
import asyncio
from os import listdir
from inspect import iscoroutinefunction
from types import ModuleType

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
