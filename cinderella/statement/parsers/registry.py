from __future__ import annotations
from typing import Dict, Type, TYPE_CHECKING

PARSERS: Dict[str, Type[StatementParser]] = {}

if TYPE_CHECKING:
    from .base import StatementParser


def register(source_name: str, cls: Type[StatementParser]) -> None:
    if source_name in PARSERS:
        raise ValueError(f"Duplicate parser for source '{source_name}'")

    PARSERS[source_name] = cls


def get_parsers() -> Dict[str, StatementParser]:
    # instantiate all parsers
    return {name: cls() for name, cls in PARSERS.items()}


def get(source_name: str) -> StatementParser:
    try:
        return PARSERS[source_name]()
    except KeyError:
        raise ValueError(f"No parser registered for source '{source_name}'")
