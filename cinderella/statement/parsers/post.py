from pathlib import Path
from typing import Optional
import pandas as pd
from datetime import datetime
from decimal import Decimal

from cinderella.ledger.datatypes import Ledger, OnExistence, StatementType
from cinderella.statement.datatypes import StatementAttributes
from .base import StatementParser


class TaiwanPost(StatementParser):
    source_name = "post"
    display_name = "TaiwanPost"
    supported_statement_types = [StatementType.checking]

    def __init__(self):
        super().__init__()

    def _read_csv(self, filepath: Path) -> pd.DataFrame:
        df = pd.read_csv(
            filepath.as_posix(),
            skipfooter=2,
            skiprows=1,
            thousands=",",
            engine="python",
        )
        df = df.replace({"=": "", '"': ""}, regex=True)
        return df

    def parse_checking_statement(
        self, records: pd.DataFrame, _: Optional[StatementAttributes] = None
    ) -> Ledger:
        records = records.fillna("").astype(str)
        typ = StatementType.checking
        ledger = Ledger(self.source_name, typ)

        prev_txn = None
        for __, record in records.iterrows():
            date_tw = record.iloc[0]
            date_to_ce = date_tw.replace(date_tw[0:3], str(int(date_tw[0:3]) + 1911))
            datetime_ = datetime.strptime(date_to_ce, "%Y/%m/%d %H:%M:%S")
            title = record.iloc[1]
            if record.iloc[3]:
                quantity = -Decimal(record.iloc[3])
            elif record.iloc[4]:
                quantity = Decimal(record.iloc[4])
            else:
                self.logger.error(
                    f"Can not parse {self.source_name} {typ.name} statement {record}"
                )
                continue

            currency = "TWD"
            account = self.statement_accounts[typ]

            if (
                prev_txn and datetime_ == prev_txn.datetime_ and quantity == 0
            ):  # duplicated record
                txn = prev_txn
            else:
                txn = ledger.create_and_append_txn(
                    datetime_, title, account, quantity, currency
                )

            # comments
            if record.iloc[6]:
                txn.insert_comment(
                    f"{self.display_name}-Remarks",
                    str(record.iloc[6]),
                    OnExistence.CONCAT,
                )
            if record.iloc[7]:
                txn.insert_comment(f"{self.display_name}-Notes", str(record.iloc[7]))

            prev_txn = txn

        return ledger
