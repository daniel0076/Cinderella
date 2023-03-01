from pathlib import Path
import pandas as pd
from datetime import datetime
from decimal import Decimal

from cinderella.ledger.datatypes import Ledger, OnExistence, StatementType
from .base import StatementParser


class TaiwanPost(StatementParser):
    source_name = "post"
    display_name = "TaiwanPost"

    def __init__(self):
        supported_types = [StatementType.bank]
        super().__init__(supported_types)

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

    def parse_bank_statement(self, records: pd.DataFrame) -> Ledger:
        records = records.fillna("").astype(str)
        typ = StatementType.bank
        ledger = Ledger(self.source_name, typ)

        prev_txn = None
        for _, record in records.iterrows():
            date_tw = record[0]
            date_to_ce = date_tw.replace(date_tw[0:3], str(int(date_tw[0:3]) + 1911))
            datetime_ = datetime.strptime(date_to_ce, "%Y/%m/%d %H:%M:%S")
            title = record[1]
            if record[3]:
                quantity = -Decimal(record[3])
            elif record[4]:
                quantity = Decimal(record[4])
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
            if record[6]:
                txn.insert_comment(
                    f"{self.display_name}-Remarks", str(record[6]), OnExistence.CONCAT
                )
            if record[7]:
                txn.insert_comment(f"{self.display_name}-Notes", str(record[7]))

            prev_txn = txn

        return ledger
