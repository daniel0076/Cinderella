import pandas as pd
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Optional

from cinderella.ledger.datatypes import Ledger, StatementType
from cinderella.statement.datatypes import StatementAttributes
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
            return self.parse_creditcard_statement(
                df, StatementAttributes(year=year, month=month)
            )

        else:
            self.logger.warning(
                f"No StatementType found for {path.as_posix()}, skipping"
            )
            return Ledger("Invalid", StatementType.invalid)

    def parse_creditcard_statement(
        self, records: pd.DataFrame, attrs: StatementAttributes
    ) -> Ledger:
        if not (attrs.year and attrs.month):
            return Ledger("Invalid", StatementType.invalid)

        records = records.astype(str)
        typ = StatementType.creditcard
        ledger = Ledger(self.source_name, typ)

        for _, record in records.iterrows():
            indicator = record["卡號末四碼"]
            if not indicator or not indicator.strip().isdigit():
                continue

            item_month, item_day = record[0].split("/", maxsplit=1)
            item_month = int(item_month)
            item_day = int(item_day)
            # 處理可能有跨年份的問題，1月帳單可能有去年12月的帳
            if attrs.month == 1 and item_month == 12:
                date = datetime(
                    year=attrs.year - 1,
                    month=item_month,
                    day=item_day,
                )
            else:
                date = datetime(attrs.year, item_month, item_day)

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

    def parse_bank_statement(
        self, records: pd.DataFrame, _: Optional[StatementAttributes] = None
    ) -> Ledger:
        records = records.fillna("").astype(str)
        typ = StatementType.bank
        ledger = Ledger(self.source_name, typ)

        for __, record in records.iterrows():
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

            operation = record[5].lstrip()
            account_number = record[6].lstrip()
            remarks = record[7].lstrip() if record[7] else ""

            title = operation
            if account_number:
                title += f"({account_number})"
            if remarks:
                title += f": {remarks}"

            currency = "TWD"
            account = self.statement_accounts[typ]

            ledger.create_and_append_txn(datetime_, title, account, quantity, currency)

        return ledger


class CathayUSD(StatementParser):
    source_name = "cathayusd"
    display_name = "Cathay"

    def __init__(self):
        supported_types = [StatementType.bank]
        super().__init__(supported_types)

    def _read_csv(self, path: Path) -> pd.DataFrame:
        df = pd.read_csv(path.as_posix(), encoding="big5")
        return df

    def parse_bank_statement(
        self, records: pd.DataFrame, _: Optional[StatementAttributes] = None
    ) -> Ledger:
        records = records.fillna("").astype(str)
        typ = StatementType.bank
        ledger = Ledger(self.source_name, typ)

        for __, record in records.iterrows():
            datetime_ = datetime.strptime(
                record[0].strip() + record[1].strip(), "%Y/%m/%d%H:%M:%S"
            )

            quantity = Decimal(record[3])
            if record[2].strip() == "存入":  # 轉出
                quantity = quantity
            else:
                quantity = -quantity

            title = record[6].strip()
            remarks = record[5].strip()

            if remarks:
                title += f": {remarks}"

            currency = "USD"
            account = self.statement_accounts[typ]

            ledger.create_and_append_txn(datetime_, title, account, quantity, currency)

        return ledger
