from enum import Enum, auto


class StatementCategory(Enum):
    ignored = auto()
    custom = auto()
    bank = auto()
    card = auto()
    receipt = auto()


class Transactions(list):
    def __init__(self, category=StatementCategory.custom, source=""):
        self.category: StatementCategory = category
        self.source = source
        super().__init__()
