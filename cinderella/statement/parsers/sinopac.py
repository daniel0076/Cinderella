from pathlib import Path
from typing import Optional
import pandas as pd
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
import re

from cinderella.ledger.datatypes import (
    Ledger,
    Amount,
    Posting,
    StatementType,
    Transaction,
    TransactionFlag,
)
from cinderella.statement.datatypes import StatementAttributes
from .base import StatementParser


class Sinopac(StatementParser):
    source_name = "sinopac"
    display_name = "SinoPac"

    def __init__(self):
        supported_types = [StatementType.bank, StatementType.creditcard]
        super().__init__(supported_types)

    def parse(self, path: Path) -> Ledger:
        if StatementType.bank.name in path.as_posix():
            try:
                df = pd.read_csv(path, encoding="big5", skiprows=2)
            except UnicodeDecodeError:
                df = pd.read_csv(path, skiprows=2)

            try:
                with open(path, "r") as f:
                    title = f.readline()
            except UnicodeDecodeError:
                with open(path, "r", encoding="big5") as f:
                    title = f.readline()

            currency = "TWD"
            if "美金" in title:
                currency = "USD"
            elif "日元" in title:
                currency = "JPY"

            df = df.replace({"\t": ""}, regex=True).fillna("").astype(str)
            return self.parse_bank_statement(df, StatementAttributes(currency=currency))

        elif StatementType.creditcard.name in path.as_posix():
            df = pd.read_csv(path)
            df = df.replace({"\t": ""}, regex=True).fillna("").astype(str)
            return self.parse_creditcard_statement(df)

        self.logger.warning(f"No StatementType found for {path.as_posix()}, skipping")
        return Ledger("Invalid", StatementType.invalid)

    def parse_creditcard_statement(
        self, records: pd.DataFrame, _: Optional[StatementAttributes] = None
    ) -> Ledger:
        category = StatementType.creditcard
        ledger = Ledger(self.source_name, StatementType.creditcard)

        currency = "TWD"
        currency_column = records.columns[4]
        if "美元" in currency_column:
            currency = "USD"

        for __, record in records.iterrows():
            date = datetime.strptime(record[0], "%Y/%m/%d")
            title = record[3].strip()
            quantity = Decimal(record[4].replace(",", ""))
            account = self.statement_accounts[category]
            ledger.create_and_append_txn(date, title, account, -quantity, currency)

        return ledger

    def parse_bank_statement(
        self, records: pd.DataFrame, attrs: StatementAttributes
    ) -> Ledger:
        if not attrs.currency:
            return Ledger("Invalid", StatementType.invalid)
        category = StatementType.bank
        ledger = Ledger(self.source_name, StatementType.bank)

        for _, record in records.iterrows():
            datetime_ = datetime.strptime(record[0].lstrip(), "%Y/%m/%d %H:%M")
            title = record[2]
            if record[3].strip() != "":  # expense
                quantity = -Decimal(record[3])
            elif record[4].strip() != "":  # income
                quantity = Decimal(record[4])
            else:
                self.logger.error(f"{self.display_name}: fail to parse {record}")
                continue
            account = self.statement_accounts[category]
            account_currency = attrs.currency

            rate = Decimal(record[6]) if record[6] else None
            if not rate:
                txn = ledger.create_and_append_txn(
                    datetime_, title, account, quantity, account_currency
                )
                txn.insert_comment(self.display_name, record[7])
                continue

            # handle currency conversion
            if attrs.currency == "TWD":
                result = re.search(r"\(([A-Z]{3,})\)", record[7])  # xxxxxx(USD)
                if result:
                    foreign_currency = result.group(1)
                else:
                    msg = f"{self.display_name}: fail to get currency {record}"
                    self.logger.error(msg)
                    continue
                postings = self._handle_bank_conversion_postings(
                    account, account, quantity, rate, attrs.currency, foreign_currency
                )
            else:
                postings = self._handle_bank_conversion_postings(
                    account, account, quantity, rate, attrs.currency, "TWD"
                )

            txn = Transaction(
                datetime_, title, postings, meta={}, flag=TransactionFlag.CONVERSIONS
            )
            ledger.append_txn(txn)

        return ledger

    def _handle_bank_conversion_postings(
        self,
        local_account: str,
        foreign_account: str,
        quantity: Decimal,
        rate: Decimal,
        local_currency: str,
        foreign_currency: str,
    ) -> list[Posting]:
        """
        SinoPac specific logic in conversion, as the statement always give the rate in
        TWD to foreign currency
        """
        price = Amount(rate, "TWD")
        if local_currency == "TWD":
            foreign_amount = Amount(
                (-quantity / rate).quantize(Decimal("0.1"), ROUND_HALF_UP),
                foreign_currency,
            )
            local_amount = Amount(quantity, local_currency)
            foreign_posting = Posting(foreign_account, foreign_amount, price)
            local_posting = Posting(local_account, local_amount)
        else:  # local non TWD, can be USD, JPY. But foreign is always TWD
            foreign_amount = Amount(
                (-quantity * rate).quantize(Decimal("0"), ROUND_HALF_UP),
                foreign_currency,
            )
            local_amount = Amount(quantity, local_currency)
            foreign_posting = Posting(foreign_account, foreign_amount)
            local_posting = Posting(local_account, local_amount, price)

        return [foreign_posting, local_posting]
