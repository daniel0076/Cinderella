import pandas as pd
from datetime import datetime
from decimal import Decimal

from datatypes import Operation, Directive, Directives, Item
from .base import StatementParser


class ESun(StatementParser):
    identifier = "esun"
    def __init__(self, config: dict = {}):
        super().__init__()
        self.default_source_accounts = {
            "bank": "Assets:Bank:ESun",
        }

    def read_statement(self, filepath: str) -> pd.DataFrame:
        df = pd.read_excel(filepath, skiprows=9, skipfooter=3, thousands=",")
        return df

    def _parse_card_statement(self, records: pd.DataFrame) -> Directives:
        raise NotImplemented

    def _parse_bank_statement(self, records: pd.DataFrame) -> Directives:
        directives = Directives("bank", self.identifier)
        for _, record in records.iterrows():
            date = record["交易日期"]
            if isinstance(record["交易日期"], str):
                # Some column has *
                date = datetime.strptime(date[1:], '%Y/%m/%d')

            if not pd.isna(record["提"]):
                amount = Decimal(str(record["提"]))
                amount *= -1
            elif not pd.isna(record["存"]):
                amount = Decimal(str(record["存"]))
            else:
                raise RuntimeError(f"Can not parse {self.identifier} statement {record}")

            title = record["摘要"]
            currency = "TWD"
            directive = Directive(date, title, amount, currency)
            directive.operations.append(
                Operation(self.default_source_accounts["bank"], amount, currency)
            )

            if not pd.isna(record["備註"]) and str(record["備註"]).strip():
                directive.items.append(Item(str(record["備註"])))

            directives.append(directive)

        return directives

    def _parse_price(self, raw_str: str) -> tuple:
        premise, amount_str = raw_str.split("$", maxsplit=1)
        amount = Decimal(amount_str.replace(",", ""))

        # used as expense, convert to positive
        if premise.startswith("-"):
            amount *= -1

        return (amount, "TWD")

    def _parse_stock_statement(self, records: list) -> Directives:
        raise NotImplemented
