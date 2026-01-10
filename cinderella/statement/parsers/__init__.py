from __future__ import annotations
import importlib
import pkgutil

# Import all modules so subclasses are created and registered
for module in pkgutil.iter_modules(__path__):
    importlib.import_module(f"{__name__}.{module.name}")
