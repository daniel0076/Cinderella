import pandas as pd
from datetime import datetime
from decimal import Decimal
import re

from cinderella.ledger.datatypes import (
    Ledger,
    Amount,
    Posting,
    StatementType,
    Transaction,
    TransactionFlag,
)
from .base import StatementParser


class Sinopac(StatementParser):
    source_name = "sinopac"
    display_name = "SinoPac"

    def __init__(self):
        supported_types = [StatementType.bank, StatementType.creditcard]
        super().__init__(supported_types)

    def _read_csv(self, filepath: str) -> pd.DataFrame:
        if "bank" in filepath:
            try:
                df = pd.read_csv(filepath, encoding="big5", skiprows=2)
            except UnicodeDecodeError:
                df = pd.read_csv(filepath, skiprows=2)
        else:
            df = pd.read_csv(filepath)

        df = df.replace({"\t": ""}, regex=True)
        return df

    def parse_creditcard_statement(self, records: pd.DataFrame) -> Ledger:
        records = records.astype(str)
        category = StatementType.creditcard
        ledger = Ledger(self.source_name, StatementType.creditcard)

        for _, record in records.iterrows():
            date = datetime.strptime(record[0], "%Y/%m/%d")
            title = record[3]
            quantity = Decimal(record[4].replace(",", ""))
            currency = "TWD"
            account = self.statement_accounts[category]
            ledger.create_and_append_txn(date, title, account, quantity, currency)

        return ledger

    def parse_bank_statement(self, records: pd.DataFrame) -> Ledger:
        records = records.astype(str)
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

            currency = "TWD"
            account = self.statement_accounts[category]

            # check currency exchange
            rate = Decimal(record[6]) if record[6].strip() != "" else None
            if rate:
                # xxxxxx(USD)
                result = re.search(r"\(([A-Z]{3,})\)", record[7])
                if result:
                    foreign_currency = result.group(1)
                else:
                    self.logger.error(
                        f"{self.display_name}: fail to get currency {record}"
                    )
                    continue

                price = Amount(rate, foreign_currency)
                amount = Amount(quantity, currency)

                posting = Posting(account, amount, price)
                txn = Transaction(
                    datetime_,
                    title,
                    [posting],
                    meta={},
                    flag=TransactionFlag.CONVERSIONS,
                )
                ledger.append_txn(txn)

            else:
                txn = ledger.create_and_append_txn(
                    datetime_, title, account, quantity, currency
                )

            txn.insert_comment(self.display_name, record[7])

        return ledger

    def parse_receipt_statement(self, _) -> Ledger:
        raise NotImplementedError(f"Receipt is not supported by {self.display_name}")
