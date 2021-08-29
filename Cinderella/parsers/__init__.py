import os
import inspect
from os.path import isfile, join, basename, dirname, realpath
from importlib import import_module

from .base import StatementParser

def get_parsers() -> list[type[StatementParser]]:

    # Auto import source modules in source/
    EXCLUDED_FILES = [basename(__file__), "base.py"]

    path = dirname(realpath(__file__))
    files_only = [file for file in os.listdir(path) if file not in EXCLUDED_FILES and isfile(join(path, file))]
    module_names = [filename.split(".")[0] for filename in files_only]

    parsers = []
    for module_name in module_names:
        module_fullname = f"parsers.{module_name}"
        module = import_module(module_fullname)
        module_classes = inspect.getmembers(module, inspect.isclass)
        for item in module_classes:
            if item[1].__module__ == module_fullname:  # our classes
                parsers.append(item[1])

    return parsers
