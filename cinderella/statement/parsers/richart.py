import pandas as pd
from datetime import datetime
from decimal import Decimal

from cinderella.ledger.datatypes import Ledger, StatementType
from .base import StatementParser


class Richart(StatementParser):
    source_name = "richart"
    display_name = "Richart"

    def __init__(self):
        self.supported_types = [StatementType.bank, StatementType.creditcard]
        # create default_accounts
        super().__init__()

    def _parse_card_statement(self, records: pd.DataFrame) -> Transactions:
        typ = StatementType.creditcard
        ledger = Ledger(self.source_name, typ)

        for _, record in records.iterrows():
            date = datetime.strptime(str(record[0]), "%Y-%m-%d")
            title = str(record[4])
            amount, currency = self._parse_price(str(record[3]))

            account = self.default_source_accounts[typ]
            transaction = self.beancount_api.make_simple_transaction(
                date, title, account, amount, currency
            )
            transactions.append(transaction)
        return transactions

    def _parse_bank_statement(self, records: pd.DataFrame) -> Transactions:
        category = StatementType.bank
        transactions = Transactions(category, self.source_name)
        for _, record in records.iterrows():
            date = datetime.strptime(str(record["交易日期"]), "%Y-%m-%d")
            title = str(record["備註"])
            amount, currency = self._parse_price(str(record["金額"]))
            account = self.default_source_accounts[category]

            transaction = self.beancount_api.make_simple_transaction(
                date, title, account, amount, currency
            )
            self.beancount_api.add_transaction_comment(transaction, str(record["摘要"]))

            transactions.append(transaction)
        return transactions

    def _parse_price(self, raw_str: str) -> tuple:
        premise, amount_str = raw_str.split("$", maxsplit=1)
        amount = Decimal(amount_str.replace(",", ""))

        # used as expense, convert to positive
        if premise.startswith("-"):
            amount *= -1

        return (amount, "TWD")
