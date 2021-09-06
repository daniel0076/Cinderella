import pandas as pd
from datetime import datetime
from decimal import Decimal

from datatypes import Transactions
from .base import StatementParser


class Taishin(StatementParser):
    identifier = "taishin"

    def __init__(self, config: dict = {}):
        super().__init__()
        self.default_source_accounts = {
            "card": "Liabilities:CreditCard:Taishin",
            "bank": "Assets:Bank:Taishin",
        }

    def _parse_card_statement(self, records: pd.DataFrame) -> Transactions:
        category = "card"
        transactions = Transactions(category, self.identifier)

        for _, record in records.iterrows():
            date = datetime.strptime(str(record[0]), "%Y/%m/%d")
            title = str(record[4])
            amount, currency = self._parse_price(str(record[3]))

            account = self.default_source_accounts[category]
            transaction = self.beancount_api.make_transaction(
                date, title, account, amount, currency
            )
            transactions.append(transaction)
        return transactions

    def _parse_bank_statement(self, records: pd.DataFrame) -> Transactions:
        transactions = Transactions("bank", self.identifier)
        for _, record in records.iterrows():
            date = datetime.strptime(str(record["交易日期"]), "%Y/%m/%d")
            title = str(record["備註"])
            amount, currency = self._parse_price(str(record["金額"]))
            account = self.default_source_accounts["bank"]

            transaction = self.beancount_api.make_transaction(
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
