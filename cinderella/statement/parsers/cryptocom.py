from pathlib import Path
from zoneinfo import ZoneInfo
from typing import Optional
import pandas as pd
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP

from cinderella.ledger.datatypes import (
    Ledger,
    StatementType,
)
from cinderella.settings import PreprocessSettings
from cinderella.statement.datatypes import ExecutionResult, StatementAttributes
from .base import StatementParser
from cinderella.statement import utils


class CryptoCom(StatementParser):
    source_name = "cryptocom"
    display_name = "CryptoCom"
    supported_statement_types = [StatementType.creditcard]

    def __init__(self):
        super().__init__()

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

    def preprocess_creditcard_statement(
        self,
        input_statement: Path,
        output_dir: Path,
        preprocess_settings: Optional[PreprocessSettings],
    ) -> ExecutionResult:

        df = pd.read_csv(input_statement, sep=",")
        for year, month, result_df in utils.split_by_year_month(df, 0):
            output_file = output_dir / f"{year}{str(month).zfill(2)}.csv"
            if output_file.exists():
                result_df = utils.merge_dataframe(output_file, result_df)

            if result_df is not None:
                result_df.to_csv(output_file, index=False)

        return ExecutionResult(True, "")  # Supress warning outside
