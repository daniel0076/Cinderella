from enum import Enum


class AfterProcessedAction(Enum):
    keep = "keep"
    move = "move"
    delete = "delete"
