from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from pandas import DataFrame

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from parsers.base import StatementParser


@dataclass
class Operation:
    account: str
    amount: Decimal = Decimal(0)
    currency: str = ""

@dataclass
class Item:
    title: str
    amount: Decimal = Decimal(0)

@dataclass
class Directive:
    date: datetime
    title: str
    amount: Decimal = Decimal(0)
    currency: str = ""
    exchange: bool = False
    operations: list[Operation] = field(default_factory=list)
    items: list[Item] = field(default_factory=list)

    def to_bean(self) -> str:
        bean_str = f'{self.date.strftime("%Y-%m-%d")} * "{self.title}"\n'

        for operation in self.operations:
            if not operation.amount and not operation.currency:
                bean_str += f"\t{operation.account}\n"
            else:
                bean_str += f"\t{operation.account} {operation.amount} {operation.currency}\n"

        for item in self.items:
            bean_str += f"\t;{item.title} {item.amount}\n"

        return bean_str

class Directives(list):
    def __init__(self, category, source):
        self.category = category
        self.source = source
        super().__init__()
