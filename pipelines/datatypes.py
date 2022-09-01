from enum import Enum


class StatementCategory(Enum):
    invalid = "invalid"
    bank = "bank"
    creditcard = "creditcard"
    receipt = "receipt"


class AfterProcessedAction(Enum):
    keep = "keep"
    move = "move"
    delete = "delete"
