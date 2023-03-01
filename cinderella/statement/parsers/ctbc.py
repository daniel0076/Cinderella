from pathlib import Path
import pandas as pd
from datetime import datetime
from decimal import Decimal
import logging

from cinderella.ledger.datatypes import Ledger, StatementType
from .base import StatementParser

# Turn off logs from pdfminer used by camelot
logging.getLogger("pdfminer").setLevel(logging.ERROR)


class CTBC(StatementParser):
    source_name = "ctbc"
    display_name = "CTBC"

    def __init__(self):
        supported_types = [StatementType.bank, StatementType.creditcard]
        super().__init__(supported_types)

    def _read_csv(self, filepath: Path) -> pd.DataFrame:
        df = pd.read_csv(
            filepath.as_posix(), encoding="big5", skiprows=2, thousands=","
        )
        return df

    def parse_bank_statement(self, records: pd.DataFrame) -> Ledger:
        records = records.fillna("").astype(str)
        typ = StatementType.bank
        ledger = Ledger(self.source_name, typ)

        for _, record in records.iterrows():
            date = datetime.strptime(record["日期"], "%Y/%m/%d")
            title = record["摘要"]
            if record["支出"]:  # spend
                quantity = -Decimal(record["支出"])
            elif record["存入"]:  # income
                quantity = Decimal(record["存入"])
            else:
                self.logger.error(
                    f"Can not parse {self.source_name} {typ.name} statement {record}"
                )
                continue

            currency = "TWD"
            account = self.statement_accounts[typ]

            txn = ledger.create_and_append_txn(date, title, account, quantity, currency)

            if record["備註"]:
                txn.insert_comment(f"{self.display_name}-Remarks", record["備註"])
            if record["轉出入帳號"]:
                txn.insert_comment(f"{self.display_name}-Acc.", record["轉出入帳號"])
            if record["註記"]:
                txn.insert_comment(f"{self.display_name}-Notes", record["註記"])

        return ledger
