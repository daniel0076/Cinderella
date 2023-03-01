import pandas as pd
from datetime import datetime
from decimal import Decimal

from cinderella.ledger.datatypes import Ledger, StatementType
from .base import StatementParser


class Richart(StatementParser):
    source_name = "richart"
    display_name = "Richart"

    def __init__(self):
        supported_types = [StatementType.bank, StatementType.creditcard]
        super().__init__(supported_types)

    def parse_creditcard_statement(self, records: pd.DataFrame) -> Ledger:
        records = records.astype(str)
        typ = StatementType.creditcard
        ledger = Ledger(self.source_name, typ)

        for _, record in records.iterrows():
            date = datetime.strptime(record[0], "%Y-%m-%d")
            title = record[4]
            quantity, currency = self._parse_price(record[3])
            account = self.statement_accounts[typ]
            ledger.create_and_append_txn(date, title, account, quantity, currency)

        return ledger

    def parse_bank_statement(self, records: pd.DataFrame) -> Ledger:
        records = records.astype(str)

        typ = StatementType.bank
        ledger = Ledger(self.source_name, typ)
        for _, record in records.iterrows():
            date = datetime.strptime(record["交易日期"], "%Y-%m-%d")
            title = record["備註"]
            quantity, currency = self._parse_price(record["金額"])
            account = self.statement_accounts[typ]

            txn = ledger.create_and_append_txn(date, title, account, quantity, currency)
            txn.insert_comment(self.display_name, record["摘要"])

        return ledger

    def _parse_price(self, raw_str: str) -> tuple:
        premise, amount_str = raw_str.split("$", maxsplit=1)
        amount = Decimal(amount_str.replace(",", ""))

        # used as expense, convert to positive
        if premise.startswith("-"):
            amount *= -1

        return (amount, "TWD")
