from datetime import datetime
from decimal import Decimal

from datatypes import Operation, Directive, Directives, Item
from .base import StatementParser


class TaiwanPost(StatementParser):
    name = "post"
    def __init__(self, config: dict = {}):
        super().__init__()
        self.default_source_accounts = {
            "bank": "Assets:Bank:Post"
        }

    def _decode_statement(self, raw_records: list[str]) -> list[str]:
        records = self._read_csv(raw_records)
        records = records[2:-1]  # trime header and footer

        clean_records = []
        for record in records:
            record = [col.replace("=", "").strip('"') for col in record]
            clean_records.append(record)

        return clean_records

    def _parse_bank_statement(self, records: list) -> Directives:
        directives = Directives("bank", self.name)
        prev_directive = Directive(datetime.now(), "init")
        for record in records:
            date_tw = record[0]
            date_to_ce = date_tw.replace(date_tw[0:3], str(int(date_tw[0:3]) + 1911))
            date = datetime.strptime(date_to_ce, '%Y/%m/%d %H:%M:%S')
            title = record[1]
            if record[3] == "":    # withdraw
                amount = Decimal(record[4].replace(",", ""))
            elif record[4] == "":  # transfer in
                amount = -Decimal(record[3].replace(",", ""))
            else:
                raise RuntimeError(f"Can not parse Taiwan Post bank statement {record}")
            currency = "TWD"

            if date == prev_directive.date and amount == 0:  # duplicated record
                directive = prev_directive
                directive.items.append(Item(title, amount))
            else:
                directive = Directive(date, title, amount, currency)
                directive.operations.append(
                    Operation(self.default_source_accounts["bank"], amount, currency)
                )
                directives.append(directive)

            if record[6] != "":
                directive.items.append(Item(record[6]))
            if record[7] != "":
                directive.items.append(Item(record[7]))

            prev_directive = directive

        return directives

