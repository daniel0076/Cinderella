import logging
import pandas as pd
import csv
from datetime import datetime
from decimal import Decimal

from cinderella.datatypes import Transactions, StatementType
from cinderella.parsers.base import StatementParser
from cinderella.settings import LOG_NAME

logger = logging.getLogger(LOG_NAME)


class Receipt(StatementParser):
    identifier = "receipt"

    def __init__(self):
        super().__init__()
        self.default_source_accounts = {StatementType.receipt: "Assets:Cash"}

    def parse(self, _: str, filepath: str) -> Transactions:
        if "invos" in filepath and "csv" in filepath:
            logger.info(f"Using Invos specification: {filepath}")
            df = pd.read_csv(filepath)
            return self._parse_receipt_invos(df)

        elif "csv" in filepath:
            df = pd.read_csv(
                filepath, delimiter="|", skiprows=2, header=None, quoting=csv.QUOTE_NONE
            )
            return self._parse_receipt(df)

        else:
            raise NotImplementedError

    def _parse_receipt(self, records: pd.DataFrame) -> Transactions:
        transactions = Transactions(StatementType.receipt, self.identifier)
        prev_transaction = None

        for _, record in records.iterrows():
            if record[0] == "M":
                date = datetime.strptime(str(record[3]), "%Y%m%d")
                title = str(record[5])
                amount = Decimal(str(record[7]))
                currency = "TWD"
                account = self.default_source_accounts[StatementType.receipt]

                transaction = self.beancount_api.make_simple_transaction(
                    date, title, account, -amount, currency
                )
                transactions.append(transaction)
                prev_transaction = transaction

            elif record[0] == "D":
                # continue on last one
                item_title = str(record[3])
                item_price = str(record[2])
                if prev_transaction:
                    self.beancount_api.add_transaction_comment(
                        prev_transaction, f"{item_title} {item_price}"
                    )

        return transactions

    def _parse_receipt_invos(self, records: pd.DataFrame) -> Transactions:
        transactions = Transactions(StatementType.receipt, self.identifier)
        prev_title, prev_date = "", datetime.now()
        prev_transaction = None

        for _, record in records.iterrows():
            date_tw = str(record[0])
            year = int(date_tw[0:-4]) + 1911
            date_str = str(year) + str(
                date_tw[::-1][0:4][::-1]
            )  # 年+月日共4位(先reverse，取4位再轉回來)

            date = datetime.strptime(date_str, "%Y%m%d")
            title = str(record["店家名稱"])
            amount = Decimal(str(record["小計"]))
            currency = "TWD"
            item_name = str(record["消費品項"])
            item_price = Decimal(str(record["單價"]))
            item_count = Decimal(str(record["個數"]))
            account = self.default_source_accounts[StatementType.receipt]

            if prev_transaction and (prev_title, prev_date) == (title, date):
                self.beancount_api.add_posting_amount(prev_transaction, -amount)
                self.beancount_api.add_transaction_comment(
                    prev_transaction, value=f"{item_name} {item_count}*{item_price}"
                )

            else:
                transaction = self.beancount_api.make_simple_transaction(
                    date, title, account, -amount, currency
                )
                self.beancount_api.add_transaction_comment(
                    transaction, value=f"{item_name}-{item_count}*{item_price}"
                )

                prev_title, prev_date = title, date
                prev_transaction = transaction
                transactions.append(transaction)

        return transactions

    def _parse_card_statement(self, records: list) -> Transactions:
        raise NotImplementedError

    def _parse_bank_statement(self, records: list) -> Transactions:
        raise NotImplementedError
