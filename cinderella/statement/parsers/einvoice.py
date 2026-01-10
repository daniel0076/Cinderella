import os
from pathlib import Path
import shutil
import pandas as pd
import csv
from datetime import datetime
from decimal import Decimal
from typing import Optional, Union

from cinderella.ledger.datatypes import Ledger, StatementType, Transaction
from cinderella.settings import PreprocessSettings
from cinderella.statement.datatypes import ExecutionResult, StatementAttributes
from .base import StatementParser


class Einvoice(StatementParser):
    source_name = "einvoice"
    display_name = "Einvoice"
    supported_statement_types = [StatementType.receipt]

    def __init__(self):
        super().__init__()

    def parse(self, filepath: Path) -> Ledger:
        if "csv" in filepath.name:
            df = pd.read_csv(
                filepath, delimiter="|", skiprows=2, header=None, quoting=csv.QUOTE_NONE
            )
            return self.parse_receipt_statement(df)
        else:
            return Ledger(self.source_name, StatementType.invalid)

    def parse_receipt_statement(
        self, records: pd.DataFrame, _: Optional[StatementAttributes] = None
    ) -> Ledger:
        records = records.astype(str)
        ledger = Ledger(self.source_name, StatementType.receipt)
        prev_txn: Union[Transaction, None] = None

        for __, record in records.iterrows():
            if record.iloc[0] == "M":
                datetime_ = datetime.strptime(record.iloc[3], "%Y%m%d")
                title = record.iloc[5]
                quantity = Decimal(record.iloc[7])
                currency = "TWD"
                account = self.statement_accounts[StatementType.receipt]

                txn = Transaction.create_simple(
                    datetime_, title, account, -quantity, currency
                )
                ledger.append_txn(txn)
                prev_txn = txn

            elif record.iloc[0] == "D":  # details on per-item info
                # continue on last one
                item_title = record.iloc[3]
                item_price = record.iloc[2]
                if prev_txn:
                    prev_txn.insert_comment(
                        self.display_name, f"{item_title} - {item_price}"
                    )

        return ledger

    def preprocess_receipt_statement(
        self,
        input_statement: Path,
        output_dir: Path,
        preprocess_settings: Optional[PreprocessSettings],
    ) -> ExecutionResult:

        # read the file, use | as delimiter and no quoting
        df: pd.DataFrame = pd.read_csv(
            input_statement,
            delimiter="|",
            skiprows=2,
            header=None,
            quoting=csv.QUOTE_NONE,
        )

        # the rows of receipt titles
        title_df = df[df[0] == "M"]

        # extract the months from the file
        months_df = title_df[3]
        months = months_df.apply(
            lambda x: str(datetime.strptime(x, "%Y%m%d").month).zfill(2)
        ).unique()

        # extract the year from the file
        one_date = months_df.iloc[0]
        year = datetime.strptime(one_date, "%Y%m%d").year

        # marshal the filename
        filename = f"{year}{''.join(months)}.csv"
        file_output = output_dir / filename

        # find the receipt ids and remove duplicated csv
        receipt_id_df = title_df[6]
        self._remove_duplicated_csv(output_dir, pd.DataFrame(receipt_id_df))

        # output the file
        if not file_output.exists():
            shutil.copy2(input_statement, file_output)
        else:
            self.logger.warning(
                f"{file_output} exists, and might containts current file content, skipping"
            )

        return ExecutionResult(True, "success")

    def _remove_duplicated_csv(self, directory: Path, receipt_id_df: pd.DataFrame):
        """
        einvoice is sent per month, but double months will containts data from last month
        read previous output files to see if this file containts those contents, if so, remove it
        """
        filenames = sorted(os.listdir(directory))
        for filename in filenames:
            if not filename.endswith("csv"):
                continue
            existing_csv = directory / filename
            existing_df = pd.read_csv(
                existing_csv,
                delimiter="|",
                skiprows=2,
                header=None,
                quoting=csv.QUOTE_NONE,
            )
            existing_title_df = existing_df[existing_df[0] == "M"]
            existing_receipt_id_df = existing_title_df[6]
            duplicated_df = receipt_id_df[receipt_id_df.isin(existing_receipt_id_df)]
            # duplication detected, remove previous file
            if len(duplicated_df) == len(existing_receipt_id_df):
                print(
                    f"preprocessor[{self.source_name}]: duplicated csv, remove {existing_csv}"
                )
                os.remove(existing_csv)
