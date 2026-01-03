from pathlib import Path
import pandas as pd
import csv
from datetime import datetime
from decimal import Decimal
from typing import Optional, Union

from cinderella.ledger.datatypes import Ledger, StatementType, Transaction
from cinderella.statement.datatypes import StatementAttributes
from .base import StatementParser


class Einvoice(StatementParser):
    source_name = "einvoice"
    display_name = "Einvoice"

    def __init__(self):
        supported_types = [StatementType.receipt]
        super().__init__(supported_types)

    def parse(self, filepath: Path) -> Ledger:
        if "csv" in filepath.name:
            df = pd.read_csv(
                filepath, delimiter="|", skiprows=2, header=None, quoting=csv.QUOTE_NONE
            )
            return self.parse_receipt_statement(df)
        else:
            return Ledger(self.source_name, StatementType.invalid)

    def parse_receipt_statement(
        self, records: pd.DataFrame, _: Optional[StatementAttributes] = None
    ) -> Ledger:
        records = records.astype(str)
        ledger = Ledger(self.source_name, StatementType.receipt)
        prev_txn: Union[Transaction, None] = None

        for __, record in records.iterrows():
            if record.iloc[0] == "M":
                datetime_ = datetime.strptime(record.iloc[3], "%Y%m%d")
                title = record.iloc[5]
                quantity = Decimal(record.iloc[7])
                currency = "TWD"
                account = self.statement_accounts[StatementType.receipt]

                txn = Transaction.create_simple(
                    datetime_, title, account, -quantity, currency
                )
                ledger.append_txn(txn)
                prev_txn = txn

            elif record.iloc[0] == "D":  # details on per-item info
                # continue on last one
                item_title = record.iloc[3]
                item_price = record.iloc[2]
                if prev_txn:
                    prev_txn.insert_comment(
                        self.display_name, f"{item_title} - {item_price}"
                    )

        return ledger
