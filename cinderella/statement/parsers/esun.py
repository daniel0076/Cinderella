from pathlib import Path
from typing import Optional
import pandas as pd
from decimal import Decimal

from cinderella.ledger.datatypes import Ledger, StatementType
from cinderella.settings import PreprocessSettings
from cinderella.statement.datatypes import ExecutionResult, StatementAttributes
from .base import StatementParser


class ESun(StatementParser):
    source_name = "esun"
    display_name = "ESun"
    supported_statement_types = [StatementType.checking]

    def __init__(self):
        super().__init__()

    def parse_checking_statement(
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

    def preprocess_checking_statement(
        self,
        input_statement: Path,
        output_dir: Path,
        preprocess_settings: Optional[PreprocessSettings],
    ) -> ExecutionResult:

        df = pd.read_html(input_statement, header=0)[1]  # The first table is useless

        df.iloc[:, 0] = df.iloc[:, 0].str.replace("*", "", regex=False)
        df.isetitem(0, pd.to_datetime(df.iloc[:, 0]))
        years = df.iloc[:, 0].dt.year.unique()
        months = df.iloc[:, 0].dt.month.unique()
        for year in years:
            for month in months:
                result_df = df.loc[
                    (df.iloc[:, 0].dt.year == year) & (df.iloc[:, 0].dt.month == month)
                ]
                if result_df.empty:
                    continue

                output_file = output_dir / f"{year}{str(month).zfill(2)}.csv"
                if output_file.exists():
                    if not self._should_replace(output_file, result_df):
                        print(f"{output_file} exists and is updated, ignored")
                        continue
                    else:
                        self.logger.warning(f"Replace {output_file} with newer records")

                print(f"output {output_file}")
                result_df.to_csv(output_file, index=False)

        return ExecutionResult(True, "")

    def _should_replace(self, target: Path, result_df: pd.DataFrame):
        existing_df = pd.read_csv(target)
        if len(existing_df) < len(result_df):
            return True

        return False
