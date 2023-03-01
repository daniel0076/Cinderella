from pathlib import Path
import pandas as pd
from datetime import datetime
from decimal import Decimal
from typing import Union

from cinderella.ledger.datatypes import Ledger, StatementType, Transaction
from .base import StatementParser


class Invos(StatementParser):
    source_name = "invos"
    display_name = "Invos"

    def __init__(self):
        supported_types = [StatementType.receipt]
        super().__init__(supported_types)

    def parse(self, filepath: Path):
        if "invos" in filepath.as_posix() and "csv" in filepath.name:
            df = pd.read_csv(filepath)
            return self.parse_receipt_statement(df)
        else:
            return Ledger(self.source_name, StatementType.invalid)

    def parse_receipt_statement(self, records: pd.DataFrame) -> Ledger:
        records = records.astype(str)
        ledger = Ledger(self.source_name, StatementType.receipt)
        prev_title, prev_datetime = "", datetime.now()
        prev_txn: Union[Transaction, None] = None

        for _, record in records.iterrows():
            date_tw = str(record[0])
            year = int(date_tw[0:-4]) + 1911
            date_str = str(year) + str(
                date_tw[::-1][0:4][::-1]
            )  # 年+月日共4位(先reverse，取4位再轉回來)

            datetime_ = datetime.strptime(date_str, "%Y%m%d")
            title = record["店家名稱"]
            quantity = Decimal(record["小計"])
            currency = "TWD"
            item_name = record["消費品項"]
            item_price = Decimal(record["單價"])
            item_count = Decimal(record["個數"])
            account = self.statement_accounts[StatementType.receipt]

            if prev_txn and (prev_title, prev_datetime) == (title, datetime_):
                txn = prev_txn
                txn.add_posting_amount(0, -quantity, currency)
            else:
                txn = ledger.create_and_append_txn(
                    datetime_, title, account, -quantity, currency
                )
                prev_title, prev_datetime = title, datetime_
                prev_txn = txn

            txn.insert_comment(
                self.display_name, f"{item_name} - {item_count}*{item_price}"
            )

        return ledger
