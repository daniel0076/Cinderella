import pandas as pd
from datetime import datetime
from decimal import Decimal

from .base import StatementParser
from datatypes import Operation, Directive, Directives, Item


class TaiwanReceipt(StatementParser):
    identifier = "receipt"
    def __init__(self):
        super().__init__()
        self.default_source_accouonts = {
            "receipt": "Assets:Cash:Wallet"
        }

    def parse(self, category: str, df: pd.DataFrame) -> Directives:
        return self._parse_receipt(df)

    def _parse_receipt(self, records: list) -> Directives:
        directives = Directives("receipt", self.identifier)

        for record in records:
            if record[0] == "M":

                date = datetime.strptime(record[3], '%Y%m%d')
                item = record[5]
                amount = Decimal(record[7])
                currency = "TWD"

                directive = Directive(date, item, amount, currency)
                directive.operations.append(
                    Operation(self.default_source_accouonts["receipt"], -amount, currency)
                )
                directives.append(directive)

            elif record[0] == "D":
                # last one is the latest one
                item_title = record[3]
                item_price = record[2]
                directives[-1].items.append(Item(item_title, item_price))

        return directives

    def _parse_card_statement(self, records: list) -> Directives:
        raise NotImplemented

    def _parse_stock_statement(self, records: list) -> Directives:
        raise NotImplemented

    def _parse_bank_statement(self, records: list) -> Directives:
        raise NotImplemented
