import logging
import pandas as pd
import csv
from datetime import datetime
from decimal import Decimal
from typing import Union

from cinderella.datatypes import Ledger, StatementType, Transaction
from cinderella.parsers.base import StatementParser
from cinderella.settings import LOG_NAME

logger = logging.getLogger(LOG_NAME)


class Receipt(StatementParser):
    identifier = "receipt"

    def __init__(self):
        super().__init__()
        self.default_source_accounts = {StatementType.receipt: "Assets:Cash"}

    def parse(self, _: str, filepath: str):
        if "invos" in filepath and "csv" in filepath:
            logger.info(f"Using Invos specification: {filepath}")
            df = pd.read_csv(filepath)
            result = self._parse_receipt_invos(df)

        elif "csv" in filepath:
            df = pd.read_csv(
                filepath, delimiter="|", skiprows=2, header=None, quoting=csv.QUOTE_NONE
            )
            result = self._parse_receipt(df)
        else:
            raise NotImplementedError

        return result.to_deprecated_transactions()

    def _parse_receipt(self, records: pd.DataFrame) -> Ledger:
        ledger = Ledger(self.identifier, StatementType.receipt)
        prev_txn: Union[Transaction, None] = None

        for _, record in records.iterrows():
            if record[0] == "M":
                datetime_ = datetime.strptime(str(record[3]), "%Y%m%d")
                title = str(record[5])
                quantity = Decimal(str(record[7]))
                currency = "TWD"
                account = self.default_source_accounts[StatementType.receipt]

                txn = Transaction.create_simple(
                    datetime_, title, account, -quantity, currency
                )
                ledger.append_txn(txn)
                prev_txn = txn

            elif record[0] == "D":
                # continue on last one
                item_title = str(record[3])
                item_price = str(record[2])
                if prev_txn:
                    prev_txn.insert_comment(
                        self.identifier, f"{item_title} {item_price}"
                    )

        return ledger

    def _parse_receipt_invos(self, records: pd.DataFrame) -> Ledger:
        ledger = Ledger(self.identifier, StatementType.receipt)
        prev_title, prev_datetime = "", datetime.now()
        prev_txn: Union[Transaction, None] = None

        for _, record in records.iterrows():
            date_tw = str(record[0])
            year = int(date_tw[0:-4]) + 1911
            date_str = str(year) + str(
                date_tw[::-1][0:4][::-1]
            )  # 年+月日共4位(先reverse，取4位再轉回來)

            datetime_ = datetime.strptime(date_str, "%Y%m%d")
            title = str(record["店家名稱"])
            money = Decimal(str(record["小計"]))
            currency = "TWD"
            item_name = str(record["消費品項"])
            item_price = Decimal(str(record["單價"]))
            item_count = Decimal(str(record["個數"]))
            account = self.default_source_accounts[StatementType.receipt]

            if prev_txn and (prev_title, prev_datetime) == (title, datetime_):
                prev_txn.add_posting_amount(0, -money, currency)
                prev_txn.insert_comment(
                    self.identifier, f"{item_name}-{item_count}*{item_price}"
                )

            else:
                txn = Transaction.create_simple(
                    datetime_, title, account, -money, currency
                )
                self.beancount_api.add_transaction_comment(
                    txn, value=f"{item_name}-{item_count}*{item_price}"
                )

                prev_title, prev_datetime = title, datetime_
                prev_txn = txn
                ledger.append_txn(txn)

        return ledger

    def _parse_card_statement(self, _) -> Ledger:
        raise NotImplementedError

    def _parse_bank_statement(self, _) -> Ledger:
        raise NotImplementedError
