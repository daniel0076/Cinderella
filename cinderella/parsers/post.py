import pandas as pd
from datetime import datetime
from decimal import Decimal

from datatypes import Transactions
from .base import StatementParser


class TaiwanPost(StatementParser):
    identifier = "post"

    def __init__(self):
        super().__init__()
        self.default_source_accounts = {"bank": "Assets:Bank:Post"}

    def _read_statement(self, filepath: str) -> pd.DataFrame:
        df = pd.read_csv(
            filepath, skipfooter=2, skiprows=1, thousands=",", engine="python"
        )
        df = df.replace({"=": "", '"': ""}, regex=True)
        return df

    def _parse_bank_statement(self, records: pd.DataFrame) -> Transactions:
        category = "bank"
        transactions = Transactions(category, self.identifier)

        prev_transaction = None
        for _, record in records.iterrows():
            date_tw = str(record[0])
            date_to_ce = date_tw.replace(date_tw[0:3], str(int(date_tw[0:3]) + 1911))
            date = datetime.strptime(date_to_ce, "%Y/%m/%d %H:%M:%S")
            title = record[1]
            if not pd.isna(record[3]):
                price = -Decimal(record[3])
            elif not pd.isna(record[4]):
                price = Decimal(record[4])
            else:
                raise RuntimeError(
                    f"Can not parse {self.identifier} {category} statement {record}"
                )
            currency = "TWD"
            account = self.default_source_accounts[category]

            if (
                prev_transaction and date == prev_transaction.date and price == 0
            ):  # duplicated record
                transaction = prev_transaction
                self.beancount_api.add_transaction_comment(
                    transaction, f"{title}-{price}"
                )
            else:
                transaction = self.beancount_api.make_transaction(
                    date, title, account, price, currency
                )
                transactions.append(transaction)

            if str(record[6]).strip():
                self.beancount_api.add_transaction_comment(transaction, str(record[6]))
            if record[7]:
                self.beancount_api.add_transaction_comment(transaction, str(record[7]))

            prev_transaction = transaction

        return transactions

    def _parse_card_statement(self, records: list) -> Transactions:
        raise NotImplementedError

    def _parse_stock_statement(self, records: list) -> Transactions:
        raise NotImplementedError
