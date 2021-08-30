import csv
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

    def _decode_statement(self, raw_records: list[str]) -> list[str]:
        records = self._read_csv(raw_records, delimiter="|")
        return records[1:]

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
