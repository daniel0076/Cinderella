from enum import Enum


class StatementType(Enum):
    invalid = "invalid"
    ignored = "ignored"
    custom = "custom"
    bank = "bank"
    creditcard = "creditcard"
    receipt = "receipt"
    stock = "stock"


class Transactions(list):
    def __init__(self, category=StatementType.custom, source: str = ""):
        self.category: StatementType = category
        self.source: str = source
        super().__init__()


class AfterProcessedAction(Enum):
    keep = "keep"
    move = "move"
    delete = "delete"
