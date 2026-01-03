from typing import Optional
import pandas as pd
from decimal import Decimal

from cinderella.ledger.datatypes import Ledger, StatementType
from cinderella.statement.datatypes import StatementAttributes
from .base import StatementParser


class ESun(StatementParser):
    source_name = "esun"
    display_name = "ESun"

    def __init__(self):
        supported_types = [StatementType.checking]
        super().__init__(supported_types)

    def parse_bank_statement(
        self, records: pd.DataFrame, _: Optional[StatementAttributes] = None
    ) -> Ledger:
        records = records.fillna("").astype(str)
        typ = StatementType.checking
        ledger = Ledger(self.source_name, typ)

        for __, record in records.iterrows():
            date = pd.to_datetime(record.iloc[0])

            if record.iloc[2]:
                quantity = Decimal(record.iloc[2])
                quantity *= -1
            elif record.iloc[3]:
                quantity = Decimal(record.iloc[3])
            else:
                self.logger.error(
                    f"Can not parse {self.source_name} {typ.name} statement {record}"
                )
                continue

            title = record.iloc[1]
            currency = "TWD"
            account = self.statement_accounts[typ]

            txn = ledger.create_and_append_txn(date, title, account, quantity, currency)

            if record.iloc[5]:
                txn.insert_comment(self.display_name, record.iloc[5])

        return ledger
