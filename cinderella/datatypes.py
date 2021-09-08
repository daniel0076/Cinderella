from enum import Enum, auto


class StatementCategory(Enum):
    custom = auto()
    bank = auto()
    card = auto()
    receipt = auto()


class Transactions(list):
    def __init__(self, category, source):
        self.category: StatementCategory = category
        self.source = source
        super().__init__()
