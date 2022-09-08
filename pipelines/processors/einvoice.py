import os
import shutil
import pandas as pd
from datetime import datetime
from pathlib import Path

from base import ProcessorBase, ProcessedResult
from settings import SourceSettings


class Einvoice(ProcessorBase):
    identifier = "einvoice"

    def __init__(
        self, output_dir_format: str, move_dir_format: str, settings: SourceSettings
    ):
        super().__init__(output_dir_format, move_dir_format, settings)

    def process_receipt(self, file: str) -> ProcessedResult:
        move_dir = Path(
            self.move_dir_format.format(
                identifier=type(self).identifier, statement_type="receipt"
            )
        )
        output_dir = Path(
            self.output_dir_format.format(
                identifier=type(self).identifier, statement_type="receipt"
            )
        )
        os.makedirs(move_dir, exist_ok=True)
        os.makedirs(output_dir, exist_ok=True)

        df = pd.read_csv(file, delimiter="|", skiprows=2, header=None)
        # the rows of receipt titles
        title_df = df[df[0] == "M"]
        months_df = title_df[3]
        one_date = months_df.iloc[0]
        year = datetime.strptime(one_date, "%Y%m%d").year
        # find the months in the file
        months = months_df.apply(
            lambda x: str(datetime.strptime(x, "%Y%m%d").month).zfill(2)
        ).unique()
        filename = f"{type(self).identifier}_{year}{''.join(months)}.csv"
        file_output = output_dir / filename
        # read the receipt ids
        receipt_id_df = title_df[6]
        self._remove_duplicated_csv(output_dir, receipt_id_df)

        # output the file
        if not file_output.exists():
            shutil.copy2(file, file_output)
        else:
            return ProcessedResult(
                False,
                f"{file_output} exists, and might containts current file content, skipping",
            )

        # move the file
        return ProcessedResult(True, "success")

    def _remove_duplicated_csv(self, directory: Path, receipt_id_df: pd.DataFrame):
        """
        einvoice is sent per month, but double months will containts data from last month
        read previous output files to see if this file containts those contents, if so, remove it
        """
        filenames = sorted(os.listdir(directory))
        for filename in filenames:
            existing_csv = directory / filename
            existing_df = pd.read_csv(
                existing_csv, delimiter="|", skiprows=2, header=None
            )
            existing_title_df = existing_df[existing_df[0] == "M"]
            existing_receipt_id_df = existing_title_df[6]
            duplicated_df = receipt_id_df[receipt_id_df.isin(existing_receipt_id_df)]
            if len(duplicated_df) == len(
                existing_receipt_id_df
            ):  # duplication detected, remove previous file
                print(f"receipt csv duplication detected, remove {existing_csv}")
                os.remove(existing_csv)

    def process_creditcard(self, file: str) -> ProcessedResult:
        return ProcessedResult(
            False, f"creditcard not supported by {type(self).identifier}"
        )

    def process_bank(self, file: str) -> ProcessedResult:
        return ProcessedResult(False, f"bank not supported by {type(self).identifier}")
