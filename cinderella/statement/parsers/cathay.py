import pandas as pd
from datetime import datetime
from decimal import Decimal
from pathlib import Path

from cinderella.ledger.datatypes import Ledger, StatementType
from .base import StatementParser


class Cathay(StatementParser):
    source_name = "cathay"
    display_name = "Cathay"

    def __init__(self):
        supported_types = [StatementType.bank, StatementType.creditcard]
        super().__init__(supported_types)

    def parse(self, path: Path) -> Ledger:
        if StatementType.bank.name in path.as_posix():
            df = pd.read_csv(
                path, encoding="big5", skiprows=1, encoding_errors="replace"
            )
            return self.parse_bank_statement(df)

        elif StatementType.creditcard.name in path.as_posix():
            # No year info in creditcard statement
            with open(path, "r", encoding="big5") as f:
                title = f.readline()
            year = int(title[0:3]) + 1911
            month = int(title.split("年")[1][0:2])
            df = pd.read_csv(
                path, encoding="big5", skiprows=20, encoding_errors="replace"
            )
            return self._parse_creditcard_statement(df, year, month)

        else:
            self.logger.warning(
                f"No StatementType found for {path.as_posix()}, skipping"
            )
            return Ledger("Invalid", StatementType.invalid)

    def _parse_creditcard_statement(
        self, records: pd.DataFrame, year: int, month: int
    ) -> Ledger:
        records = records.astype(str)
        typ = StatementType.creditcard
        ledger = Ledger(self.source_name, typ)

        for _, record in records.iterrows():
            indicator = record["卡號末四碼"]
            if pd.isna(indicator) or not indicator.strip().isdigit():
                continue

            item_month, item_day = record[0].split("/", maxsplit=1)
            item_month = int(item_month)
            item_day = int(item_day)
            # 處理可能有跨年份的問題，1月帳單可能有去年12月的帳
            if month == 1 and item_month == 12:
                date = datetime(
                    year=year - 1,
                    month=item_month,
                    day=item_day,
                )
            else:
                date = datetime(year, item_month, item_day)

            title = record["交易說明"].strip()
            currency = "TWD"
            quantity = -1 * Decimal(record["臺幣金額"])
            account = self.statement_accounts[typ]

            txn = ledger.create_and_append_txn(date, title, account, quantity, currency)

            if record["外幣金額"].strip():
                txn.insert_comment(
                    self.display_name, f"{record['幣別']}-{record['外幣金額']}"
                )

        return ledger

    def parse_bank_statement(self, records: pd.DataFrame) -> Ledger:
        records = records.astype(str)
        typ = StatementType.bank
        ledger = Ledger(self.source_name, typ)

        for _, record in records.iterrows():
            datetime_ = datetime.strptime(record[0] + record[1], "%Y%m%d%H%M%S")

            if record[2].strip():  # 轉出
                quantity = Decimal(record[2])
                quantity *= -1
            elif record[3].strip():  # 轉入
                quantity = Decimal(record[3])
            else:
                self.logger.error(
                    f"Can not parse {self.source_name} {typ.name} statement {record}"
                )
                continue

            remarks = record[7].lstrip() if not pd.isna(record[7]) else ""
            info = record[6].lstrip()
            explanation = record[5]

            if remarks:
                title = remarks
                extra = f"{explanation}-{info}"
            else:
                title = info
                extra = explanation

            currency = "TWD"
            account = self.statement_accounts[typ]

            txn = ledger.create_and_append_txn(
                datetime_, title, account, quantity, currency
            )
            txn.insert_comment(self.display_name, extra)

        return ledger

    def parse_creditcard_statement(self, _) -> Ledger:
        raise NotImplementedError(
            f"{self.display_name} has specialized creditcard parser"
        )

    def parse_receipt_statement(self, _) -> Ledger:
        raise NotImplementedError(f"Receipt is not supported by {self.display_name}")
