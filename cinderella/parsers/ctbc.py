import pandas as pd
import numpy as np
from datetime import datetime
from decimal import Decimal
import logging

from cinderella.datatypes import Transactions, StatementCategory
from cinderella.parsers.base import StatementParser

# Turn off logs from pdfminer used by camelot
logging.getLogger("pdfminer").setLevel(logging.ERROR)


class CTBC(StatementParser):
    identifier = "ctbc"

    def __init__(self):
        super().__init__()
        self.default_source_accounts = {
            StatementCategory.card: "Liabilities:CreditCard:CTBC",
            StatementCategory.bank: "Assets:Bank:CTBC",
        }

    def _read_statement(self, filepath: str) -> pd.DataFrame:
        df = pd.read_csv(filepath, encoding="big5", skiprows=2, thousands=",")
        return df

    def _parse_card_statement(self, records: pd.DataFrame) -> Transactions:
        category = StatementCategory.bank
        transactions = Transactions(category, self.identifier)
        return transactions

    def _parse_bank_statement(self, records: pd.DataFrame) -> Transactions:
        category = StatementCategory.bank
        transactions = Transactions(category, self.identifier)

        for _, record in records.iterrows():
            date = datetime.strptime(record["日期"], "%Y/%m/%d")
            title = record["摘要"]
            if not np.isnan(record["支出"]):  # spend
                price = -Decimal(record["支出"])
            elif not np.isnan(record["存入"]):  # income
                price = Decimal(record["存入"])
            else:
                raise RuntimeError(
                    f"Can not parse {self.identifier} {category.name} statement {record}"
                )

            currency = "TWD"
            account = self.default_source_accounts[category]

            transaction = self.beancount_api.make_simple_transaction(
                date, title, account, price, currency
            )
            comment = ""
            if not pd.isna(record["備註"]):
                comment += str(record["備註"])
            if not pd.isna(record["轉出入帳號"]):
                comment += str(record["轉出入帳號"])
            if not pd.isna(record["註記"]):
                comment += str(record["註記"])

            if comment:
                self.beancount_api.add_transaction_comment(transaction, comment)

            transactions.append(transaction)

        return transactions
