import pandas as pd
from datetime import datetime
from decimal import Decimal

from datatypes import Operation, Directive, Directives, Item
from .base import StatementParser


class Sinopac(StatementParser):
    identifier = "sinopac"
    def __init__(self, config: dict = {}):
        super().__init__()
        self.default_source_accounts = {
            "card": "Liabilities:CreditCard:Sinopac",
            "bank": "Assets:Bank:Sinopac"
        }

    def read_statement(self, filepath: str) -> pd.DataFrame:
        try:
            df = pd.read_csv(filepath, encoding="big5", skiprows=2, thousands=".")
        except UnicodeDecodeError:
            df = pd.read_csv(filepath, thousands=".")
        return df

    def _parse_card_statement(self, records: list) -> Directives:
        directives = Directives("card", self.identifier)
        for _, record in records.iterrows():
            date = datetime.strptime(record[0].lstrip().replace("\ufeff", ""), '%Y/%m/%d')
            title = record[3]
            amount = Decimal(record[4].replace(",", ""))
            currency = "TWD"

            directive = Directive(date, title, amount, currency)
            directive.operations.append(
                Operation(self.default_source_accounts["card"], -amount, currency)
            )
            directives.append(directive)

        return directives

    def _parse_bank_statement(self, records: list) -> Directives:
        directives = Directives("bank", self.identifier)
        for _, record in records.iterrows():
            date = datetime.strptime(record[1].lstrip(), '%Y/%m/%d')
            title = record[2]
            if record[3] == " ":
                amount = Decimal(record[4])
            elif record[4] == " ":
                amount = -Decimal(record[3])
            else:
                raise RuntimeError(f"Can not parse Sinopac bank statement {record}")
            currency = "TWD"

            directive = Directive(date, title, amount, currency)
            directive.operations.append(
                Operation(self.default_source_accounts["bank"], amount, currency)
            )
            directive.items.append(Item(str(record[7])))

            directives.append(directive)

        return directives

    def _parse_stock_statement(self, records: list) -> Directives:
        raise NotImplemented

