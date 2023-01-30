import pandas as pd
from datetime import datetime
from decimal import Decimal

from cinderella.datatypes import Transactions, StatementType
from cinderella.parsers.base import StatementParser


class Richart(StatementParser):
    identifier = "richart"

    def __init__(self, config: dict = {}):
        super().__init__()
        self.default_source_accounts = {
            StatementType.creditcard: "Liabilities:CreditCard:Richart",
            StatementType.bank: "Assets:Bank:Richart",
        }

    def _parse_card_statement(self, records: pd.DataFrame) -> Transactions:
        category = StatementType.creditcard
        transactions = Transactions(category, self.identifier)

        for _, record in records.iterrows():
            date = datetime.strptime(str(record[0]), "%Y-%m-%d")
            title = str(record[4])
            amount, currency = self._parse_price(str(record[3]))

            account = self.default_source_accounts[category]
            transaction = self.beancount_api.make_simple_transaction(
                date, title, account, amount, currency
            )
            transactions.append(transaction)
        return transactions

    def _parse_bank_statement(self, records: pd.DataFrame) -> Transactions:
        category = StatementType.bank
        transactions = Transactions(category, self.identifier)
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
