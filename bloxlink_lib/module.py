from typing import Callable, Coroutine, Any
import importlib
import logging
import asyncio
from os import listdir, path
from inspect import iscoroutinefunction
from types import ModuleType


deferred_module_functions: list[Callable, Coroutine] = []


def execute_deferred_module_functions(*args):
    """Executes deferred module functions. This should be called AFTER all modules loaded."""

    logging.debug("Executing deferred module functions")

    for deferred_function in deferred_module_functions:
        try:
            if iscoroutinefunction(deferred_function):
                try:
                    asyncio.run(deferred_function(*args))
                except RuntimeError:
                    asyncio.create_task(deferred_function(*args))
            else:
                deferred_function(*args)
        except Exception as e: # pylint: disable=broad-except
            logging.error(f"Module __defer__ function errored: {e}")

    deferred_module_functions.clear()

def load_module(import_name: str, *args) -> ModuleType:
    """Utility function to import python modules.

    Args:
        import_name (str): Name of the module to import
        *args: Arguments to pass to the __setup__ function
    """

    logging.info(f"Attempting to load module {import_name}")

    try:
        module = importlib.import_module(import_name)

    except (ImportError, ModuleNotFoundError) as e:
        logging.error(f"Failed to import {import_name}: {e}")
        raise

    except Exception as e:
        logging.error(f"Module {import_name} errored: {e}")
        logging.exception(e)
        raise

    if hasattr(module, "__setup__"):
        try:
            if iscoroutinefunction(module.__setup__):
                asyncio.run(module.__setup__(*args))
            else:
                module.__setup__(*args)

        except Exception as e:
            logging.error(f"Module {import_name} __setup__ function errored: {e}")
            logging.exception(e)
            raise e

    if hasattr(module, "__defer__"):
        logging.info(f"Deferring module {import_name} __defer__ function")
        deferred_module_functions.append(module.__defer__)

    logging.info(f"Loaded module {import_name}")

    return module

def load_modules(*paths: tuple[str], starting_path: str=".", execute_deferred_modules: bool = True, init_functions: list[Any]=None) -> list[ModuleType]:
    """Utility function to import python modules.

    Args:
        paths (list[str]): Paths of modules to import
        starting_path (str): Path to start from
        execute_deferred_modules (bool): Whether to execute deferred modules
        init_functions (list[Any]): Passed to setup and deferred functions
    """

    modules: list[ModuleType] = []
    init_functions = init_functions or []

    for directory in paths:
        files = [
            name
            for name in listdir(starting_path + directory.replace(".", "/"))
            if name[:1] != "." and name[:2] != "__" and name != "_DS_Store"
        ]

        for filename in [f.replace(".py", "") for f in files]:
            if filename in ("__main__", "__init__"):
                continue

            if path.isdir(f"{starting_path}{directory}/{filename}".replace(".", "/")):
                modules += load_modules(f"{directory}.{filename}", starting_path=starting_path, execute_deferred_modules=False)

            module = load_module(f"{directory}.{filename}", *init_functions)

            if module:
                modules.append(module)

    if execute_deferred_modules:
        execute_deferred_module_functions(*init_functions)

    return modules

def defer_execution(func: Callable):
    """Decorator to defer module functions."""

    deferred_module_functions.append(func)
    return func
