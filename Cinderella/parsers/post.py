import pandas as pd
from datetime import datetime
from decimal import Decimal

from datatypes import Operation, Directive, Directives, Item
from .base import StatementParser


class TaiwanPost(StatementParser):
    identifier = "post"
    def __init__(self):
        super().__init__()
        self.default_source_accounts = {
            "bank": "Assets:Bank:Post"
        }

    def read_statement(self, filepath: str) -> pd.DataFrame:
        df = pd.read_csv(filepath, skipfooter=2, skiprows=1, thousands=",", engine="python")
        df = df.replace({"=":"", '"':''}, regex= True)
        return df

    def _parse_bank_statement(self, records: list) -> Directives:
        directives = Directives("bank", self.identifier)
        prev_directive = Directive(datetime.now(), "init")
        for _, record in records.iterrows():
            date_tw = record[0]
            date_to_ce = date_tw.replace(date_tw[0:3], str(int(date_tw[0:3]) + 1911))
            date = datetime.strptime(date_to_ce, '%Y/%m/%d %H:%M:%S')
            title = record[1]
            if not pd.isnull(record[3]):
                amount = -Decimal(record[3])
            elif not pd.isnull(record[4]):
                amount = Decimal(record[4])
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

            if record[6]:
                directive.items.append(Item(str(record[6])))
            if record[7]:
                directive.items.append(Item(str(record[7])))

            prev_directive = directive

        return directives

    def _parse_card_statement(self, records: list) -> Directives:
        raise NotImplemented

    def _parse_stock_statement(self, records: list) -> Directives:
        raise NotImplemented
