from enum import Enum


class StatementCategory(Enum):
    ignored = "ignored"
    custom = "custom"
    bank = "bank"
    card = "card"
    receipt = "receipt"
    stock = "stock"


class Transactions(list):
    def __init__(self, category=StatementCategory.custom, source=""):
        self.category: StatementCategory = category
        self.source = source
        super().__init__()


class AfterProcessedAction(Enum):
    keep = "keep"
    move = "move"
    delete = "delete"

