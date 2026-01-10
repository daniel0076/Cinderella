from enum import Enum
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Generic, Optional, Type, TypeVar, Union

from lxml.html.builder import B


@dataclass
class PreprocessResult:
    processed_files: list[Path]

    def __post_init__(self):
        for file in self.processed_files:
            if not isinstance(file, Path):
                raise TypeError(
                    f"Expected Path type in processed_files, got {type(file)}"
                )
            if not file.exists():
                raise ValueError(f"Processed file {file.as_posix()} does not exist")


MessageT = TypeVar("MessageT")


@dataclass
class ExecutionResult(Generic[MessageT]):
    success: bool
    message: Optional[MessageT] = None


class AfterPreprocessAction(Enum):
    keep = "keep"
    move = "move"
    delete = "delete"


@dataclass
class StatementAttributes:
    """
    StatementAttributes infered on reading a statement file, which is used to assist
    the follow up parsing as the table may not contain all the information required
    """

    year: Optional[int] = None
    month: Optional[int] = None
    currency: Optional[str] = None
