from enum import Enum
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Generic, Optional, Type, TypeVar, Union

from lxml.html.builder import B


MessageT = TypeVar("MessageT")


@dataclass
class ExecutionResult(Generic[MessageT]):
    success: bool
    message: Optional[MessageT] = None


@dataclass
class StatementAttributes:
    """
    StatementAttributes infered on reading a statement file, which is used to assist
    the follow up parsing as the table may not contain all the information required
    """

    year: Optional[int] = None
    month: Optional[int] = None
    currency: Optional[str] = None
