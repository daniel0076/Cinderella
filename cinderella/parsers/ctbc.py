import pandas as pd
from datetime import datetime
from decimal import Decimal
import logging

import camelot

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
        if filepath.endswith(".pdf"):
            tables = camelot.read_pdf(filepath, process_background=True)

            df = tables[0].df
            df = df.replace({"[ ]": ""}, regex=True)
            df[2] = df[2].replace({"[\n]": ""}, regex=True)  # title
            df[6] = df[6].replace({"[\n]": ", "}, regex=True)  # comment
            df.iloc[:, 3:6] = df.iloc[:, 3:6].replace({",": ""}, regex=True)  # amounts

        elif filepath.endswith(".pdf"):
            print("error, not supported")
            df = pd.DataFrame([])

        return df

    def _parse_card_statement(self, records: pd.DataFrame) -> Transactions:
        raise NotImplementedError

    def _parse_bank_statement(self, records: pd.DataFrame) -> Transactions:
        category = StatementCategory.bank
        transactions = Transactions(category, self.identifier)

        for _, record in records.iterrows():
            if record[1] == "":
                continue

            date = datetime.strptime(record[1], "%Y/%m/%d")
            title = record[2]
            if record[3] != "":  # spend
                price = -Decimal(record[3])
            elif record[4] != "":  # income
                price = Decimal(record[4])
            else:
                raise RuntimeError(
                    f"Can not parse {self.identifier} {category.name} statement {record}"
                )

            currency = "TWD"
            account = self.default_source_accounts[category]

            transaction = self.beancount_api.make_transaction(
                date, title, account, price, currency
            )
            self.beancount_api.add_transaction_comment(transaction, f"{record[6]}")

            transactions.append(transaction)

        return transactions
