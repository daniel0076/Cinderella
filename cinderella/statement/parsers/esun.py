import pandas as pd
from decimal import Decimal

from cinderella.statement.datatypes import Transactions, StatementType
from cinderella.parsers.base import StatementParser


class ESun(StatementParser):
    identifier = "esun"

    def __init__(self, config: dict = {}):
        super().__init__()
        self.default_source_accounts = {
            StatementType.bank: "Assets:Bank:ESun",
        }

    def _parse_card_statement(self, records: pd.DataFrame) -> Transactions:
        raise NotImplementedError

    def _parse_bank_statement(self, records: pd.DataFrame) -> Transactions:
        category = StatementType.bank
        transactions = Transactions(category, self.identifier)

        for _, record in records.iterrows():
            date = pd.to_datetime(record[0])

            if not pd.isna(record[2]):
                price = Decimal(record[2])
                price *= -1
            elif not pd.isna(record[3]):
                price = Decimal(record[3])
            else:
                raise RuntimeError(
                    f"Can not parse {self.identifier} {category.name} statement {record}"
                )

            title = str(record[1])
            currency = "TWD"
            account = self.default_source_accounts[category]

            transaction = self.beancount_api.make_simple_transaction(
                date, title, account, price, currency
            )

            comment = ""
            if not pd.isna(record[5]):
                comment += str(record[5])

            if comment:
                self.beancount_api.add_transaction_comment(transaction, comment)

            transactions.append(transaction)

        return transactions

    def _parse_stock_statement(self, records: list) -> Transactions:
        raise NotImplementedError
