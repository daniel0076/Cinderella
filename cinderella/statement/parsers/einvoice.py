import pandas as pd
import csv
from datetime import datetime
from decimal import Decimal
from typing import Union

from cinderella.ledger.datatypes import Ledger, StatementType, Transaction
from .base import StatementParser


class Einvoice(StatementParser):
    source_name = "einvoice"
    display_name = "Einvoice"

    def __init__(self):
        supported_types = [StatementType.receipt]
        super().__init__(supported_types)

    def parse(self, _: str, filepath: str) -> Ledger:
        if "csv" in filepath:
            df = pd.read_csv(
                filepath, delimiter="|", skiprows=2, header=None, quoting=csv.QUOTE_NONE
            )
            return self.parse_receipt_statement(df)
        else:
            return Ledger(self.source_name, StatementType.invalid)

    def parse_receipt_statement(self, records: pd.DataFrame) -> Ledger:
        records = records.astype(str)
        ledger = Ledger(self.source_name, StatementType.receipt)
        prev_txn: Union[Transaction, None] = None

        for _, record in records.iterrows():
            if record[0] == "M":
                datetime_ = datetime.strptime(record[3], "%Y%m%d")
                title = record[5]
                quantity = Decimal(record[7])
                currency = "TWD"
                account = self.statement_accounts[StatementType.receipt]

                txn = Transaction.create_simple(
                    datetime_, title, account, -quantity, currency
                )
                ledger.append_txn(txn)
                prev_txn = txn

            elif record[0] == "D":  # details on per-item info
                # continue on last one
                item_title = record[3]
                item_price = record[2]
                if prev_txn:
                    prev_txn.insert_comment(
                        self.display_name, f"{item_title} - {item_price}"
                    )

        return ledger

    def parse_creditcard_statement(self, _) -> Ledger:
        raise NotImplementedError

    def parse_bank_statement(self, _) -> Ledger:
        raise NotImplementedError
