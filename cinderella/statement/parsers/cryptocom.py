from zoneinfo import ZoneInfo
from typing import Optional
import pandas as pd
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP

from cinderella.ledger.datatypes import (
    Ledger,
    StatementType,
)
from cinderella.statement.datatypes import StatementAttributes
from .base import StatementParser


class CryptoCom(StatementParser):
    source_name = "cryptocom"
    display_name = "CryptoCom"

    def __init__(self):
        supported_types = [StatementType.creditcard]
        super().__init__(supported_types)

    def parse_creditcard_statement(
        self, records: pd.DataFrame, _: Optional[StatementAttributes] = None
    ) -> Ledger:
        category = StatementType.creditcard
        ledger = Ledger(self.source_name, StatementType.creditcard)

        records = records.fillna("").astype(str)
        taiwan_tz = ZoneInfo("Asia/Taipei")

        for __, record in records.iterrows():
            date = datetime.strptime(record.iloc[0], "%Y-%m-%d %H:%M:%S").astimezone(
                taiwan_tz
            )
            title = record.iloc[1].strip()

            if record.iloc[5] != "":
                cost = f"({record.iloc[5]} {record.iloc[4]})"
            else:
                cost = f"({record.iloc[3]} {record.iloc[2]})"
            title += f" {cost}"

            quantity = Decimal(record.iloc[8]).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
            currency = "USD"
            account = self.statement_accounts[category]
            ledger.create_and_append_txn(date, title, account, quantity, currency)

        return ledger
