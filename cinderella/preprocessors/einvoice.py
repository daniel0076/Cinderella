import os
import shutil
import pandas as pd
import logging
from datetime import datetime
from pathlib import Path

from cinderella.preprocessors.base import ProcessorBase, ProcessedResult
from cinderella.settings import RawStatementProcessSettings, LOG_NAME
from cinderella.datatypes import StatementType

logger = logging.getLogger(LOG_NAME)


class Einvoice(ProcessorBase):
    source_name = "einvoice"

    def process_receipt(
        self, file: Path, settings: RawStatementProcessSettings
    ) -> ProcessedResult:
        # ensure the directory exists
        output_dir = Path(
            self.output_dir, StatementType.receipt.value, type(self).source_name
        )

        os.makedirs(output_dir, exist_ok=True)

        # read the file
        df: pd.DataFrame = pd.read_csv(file, delimiter="|", skiprows=2, header=None)

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
        self._remove_duplicated_csv(output_dir, receipt_id_df)

        # output the file
        if not file_output.exists():
            shutil.copy2(file, file_output)
        else:
            logger.warning(
                f"{file_output} exists, and might containts current file content, skipping"
            )

        return ProcessedResult(True, "success")

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
                existing_csv, delimiter="|", skiprows=2, header=None
            )
            existing_title_df = existing_df[existing_df[0] == "M"]
            existing_receipt_id_df = existing_title_df[6]
            duplicated_df = receipt_id_df[receipt_id_df.isin(existing_receipt_id_df)]
            # duplication detected, remove previous file
            if len(duplicated_df) == len(existing_receipt_id_df):
                print(f"csv duplication detected, remove {existing_csv}")
                os.remove(existing_csv)

    def process_creditcard(
        self, file: Path, settings: RawStatementProcessSettings
    ) -> ProcessedResult:
        return ProcessedResult(
            False, f"creditcard not supported by {type(self).source_name}"
        )

    def process_bank(
        self, file: Path, settings: RawStatementProcessSettings
    ) -> ProcessedResult:
        return ProcessedResult(False, f"bank not supported by {type(self).source_name}")
