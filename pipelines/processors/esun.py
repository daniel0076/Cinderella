import os
import pandas as pd
import logging
from pathlib import Path


from base import ProcessorBase, ProcessedResult
from settings import SourceSettings, StatementCategory

LOGGER = logging.getLogger(__name__)


class ESun(ProcessorBase):
    source_name = "esun"

    def __init__(
        self, output_dir_format: str, move_dir_format: str, settings: SourceSettings
    ):
        super().__init__(output_dir_format, move_dir_format, settings)

    def process_receipt(self, file: Path) -> ProcessedResult:
        return ProcessedResult(
            False, f"{file} not supported by {type(self).source_name}"
        )

    def process_creditcard(self, file: Path) -> ProcessedResult:
        return ProcessedResult(
            False, f"{file} not supported by {type(self).source_name}"
        )

    def process_bank(self, file: Path) -> ProcessedResult:
        # ensure the directory exists
        output_dir = Path(
            self.output_dir_format.format(
                source_name=type(self).source_name,
                statement_type=StatementCategory.bank.value,
            )
        )
        os.makedirs(output_dir, exist_ok=True)

        df = pd.read_html(file, header=0)[1]  # The first table is useless

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
                        LOGGER.warning(f"Replace {output_file} with newer records")

                print(f"output {output_file}")
                result_df.to_csv(output_file, index=False)

        return ProcessedResult(True, "")

    def _should_replace(self, target: Path, result_df: pd.DataFrame):
        existing_df = pd.read_csv(target)
        if len(existing_df) < len(result_df):
            return True

        return False
