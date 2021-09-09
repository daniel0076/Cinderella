import pandas as pd
from datetime import datetime
from decimal import Decimal

from cinderella.datatypes import Transactions, StatementCategory
from cinderella.parsers.base import StatementParser


class Sinopac(StatementParser):
    identifier = "sinopac"

    def __init__(self, config: dict = {}):
        super().__init__()
        self.default_source_accounts = {
            StatementCategory.card: "Liabilities:CreditCard:Sinopac",
            StatementCategory.bank: "Assets:Bank:Sinopac",
        }

    def _read_statement(self, filepath: str) -> pd.DataFrame:
        try:
            df = pd.read_csv(filepath, encoding="big5", skiprows=2)
        except UnicodeDecodeError:
            df = pd.read_csv(filepath)
        df = df.replace({"\t": ""}, regex=True)
        df = df.applymap(str)
        return df

    def _parse_card_statement(self, records: list) -> Transactions:
        category = StatementCategory.card
        transactions = Transactions(category, self.identifier)

        for _, record in records.iterrows():
            date = datetime.strptime(record[0], "%Y/%m/%d")
            title = record[3]
            price = Decimal(record[4].replace(",", ""))
            currency = "TWD"
            account = self.default_source_accounts[category]

            transaction = self.beancount_api.make_transaction(
                date, title, account, -price, currency
            )
            transactions.append(transaction)

        return transactions

    def _parse_bank_statement(self, records: list) -> Transactions:
        category = StatementCategory.bank
        transactions = Transactions(category, self.identifier)

        for _, record in records.iterrows():
            date = datetime.strptime(record[1].lstrip(), "%Y/%m/%d")
            title = record[2]
            if record[3] == " ":
                price = Decimal(record[4])
            elif record[4] == " ":
                price = -Decimal(record[3])
            else:
                raise RuntimeError(
                    f"Can not parse {self.identifier} {category.name} statement {record}"
                )

            currency = "TWD"
            account = self.default_source_accounts[category]

            transaction = self.beancount_api.make_transaction(
                date, title, account, price, currency
            )
            # can be exchange rate
            rate = Decimal(str(record[6])) if not pd.isna(record[6]) else None
            if rate:
                self.beancount_api.add_transaction_comment(
                    transaction, f"{record[7]} {rate}"
                )

            transactions.append(transaction)

        return transactions
