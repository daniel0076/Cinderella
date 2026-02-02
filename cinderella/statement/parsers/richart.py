import os
from pathlib import Path
from typing import Optional
import zipfile
import pandas as pd
from datetime import datetime
from decimal import Decimal

from cinderella.ledger.datatypes import Ledger, StatementType
from cinderella.settings import PreprocessSettings
from cinderella.statement.datatypes import (
    ExecutionResult,
    StatementAttributes,
)
from .base import StatementParser


class Richart(StatementParser):
    source_name = "richart"
    display_name = "Richart"
    supported_statement_types = [StatementType.checking, StatementType.creditcard]

    def __init__(self):
        super().__init__()

    def parse_creditcard_statement(
        self, records: pd.DataFrame, _: Optional[StatementAttributes] = None
    ) -> Ledger:
        records = records.astype(str)
        typ = StatementType.creditcard
        ledger = Ledger(self.source_name, typ)

        for __, record in records.iterrows():
            date = datetime.strptime(record.iloc[0], "%Y-%m-%d")
            title = record.iloc[4]
            quantity, currency = self._parse_price(record.iloc[3])
            account = self.statement_accounts[typ]
            ledger.create_and_append_txn(date, title, account, quantity, currency)

        return ledger

    def parse_checking_statement(
        self, records: pd.DataFrame, _: Optional[StatementAttributes] = None
    ) -> Ledger:
        records = records.astype(str)

        typ = StatementType.checking
        ledger = Ledger(self.source_name, typ)
        for __, record in records.iterrows():
            # 台新用帳務日期欄位做為當下，交易日期可能較晚
            date = datetime.strptime(record.iloc[1], "%Y-%m-%d")
            title = record["備註"]
            quantity, currency = self._parse_price(record["金額"])
            account = self.statement_accounts[typ]

            txn = ledger.create_and_append_txn(date, title, account, quantity, currency)
            txn.insert_comment(self.display_name, record["摘要"])

        return ledger

    def _parse_price(self, raw_str: str) -> tuple:
        premise, amount_str = raw_str.split("$", maxsplit=1)
        amount = Decimal(amount_str.replace(",", ""))

        # used as expense, convert to positive
        if premise.startswith("-"):
            amount *= -1

        return (amount, "TWD")

    def preprocess_creditcard_statement(
        self,
        input_statement: Path,
        output_dir: Path,
        preprocess_settings: Optional[PreprocessSettings],
    ) -> ExecutionResult:
        return self._preprocess_common(input_statement, output_dir, preprocess_settings)

    def preprocess_checking_statement(
        self,
        input_statement: Path,
        output_dir: Path,
        preprocess_settings: PreprocessSettings | None,
    ) -> ExecutionResult:
        return self._preprocess_common(input_statement, output_dir, preprocess_settings)

    def _preprocess_common(
        self,
        input_statement: Path,
        output_dir: Path,
        preprocess_settings: Optional[PreprocessSettings],
    ) -> ExecutionResult:
        """
        Richart has bank and creditcard in the same file
        """

        if preprocess_settings is None:
            return ExecutionResult(
                False,
                f"preprocess settings is required for {type(self).source_name} creditcard as the file is encrypted",
            )

        if not zipfile.is_zipfile(input_statement):
            return ExecutionResult(False, f"{input_statement} is not a valid zip file")

        with zipfile.ZipFile(input_statement) as zipfp:
            filename = zipfp.namelist()[0]  # only contains one file
            with zipfp.open(filename, pwd=preprocess_settings.password.encode()) as fp:
                # 0 for creditcard, 1 for bank
                creditcard_df = pd.read_excel(fp, sheet_name=0)
                bank_df = pd.read_excel(fp, sheet_name=1)

        checking_account_result = self._split_by_year_month(
            bank_df, StatementType.checking, output_dir
        )
        creditcard_result = self._split_by_year_month(
            creditcard_df, StatementType.creditcard, output_dir
        )

        if not checking_account_result.success:
            self.logger.error(checking_account_result.message)
        if not creditcard_result.success:
            self.logger.error(creditcard_result.message)

        # Supress warning outside
        return ExecutionResult(True, "")

    def _split_by_year_month(
        self, df: pd.DataFrame, statement_type: StatementType, output_dir: Path
    ) -> ExecutionResult:
        os.makedirs(output_dir, exist_ok=True)

        df[df.columns[0]] = pd.to_datetime(df.iloc[:, 0])
        df[df.columns[1]] = pd.to_datetime(df.iloc[:, 1])
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
                        continue
                    else:
                        print(f"Update {output_file} with newer records")

                result_df.to_csv(output_file, index=False)

        return ExecutionResult(True, "")

    def _should_replace(self, target: Path, result_df: pd.DataFrame):
        existing_df = pd.read_csv(target)
        if len(existing_df) < len(result_df):
            return True

        return False
