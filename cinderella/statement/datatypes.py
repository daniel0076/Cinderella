from enum import Enum
from dataclasses import dataclass
from typing import Optional


class AfterProcessedAction(Enum):
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
