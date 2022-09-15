import os
import shutil
import pandas as pd
import logging
import zipfile
from datetime import datetime
from pathlib import Path


from base import ProcessorBase, ProcessedResult
from settings import SourceSettings, StatementCategory

LOGGER = logging.getLogger(__name__)


class Richart(ProcessorBase):
    source_name = "richart"

    def __init__(
        self, output_dir_format: str, move_dir_format: str, settings: SourceSettings
    ):
        super().__init__(output_dir_format, move_dir_format, settings)

    def process(self, file: Path) -> ProcessedResult:
        """
        Overrides the default process, as Richart has bank and creditcard in the same file, process them together
        """
        all_success = True
        for statement in self.settings.statements:
            result = self._process_combined_file(file, statement.type)
            if not result.success:
                all_success = False
                LOGGER.error(result.message)

        if all_success:
            for statement in self.settings.statements:
                # execute action after processed
                self.post_process(file, statement.type)

        return ProcessedResult(True, "")  # Supress warning outside

    def process_receipt(self, file: Path) -> ProcessedResult:
        return ProcessedResult(False, f"{file} not supported by {type(self).source_name}")

    def process_creditcard(self, file: Path) -> ProcessedResult:
        """
        Richart has bank and creditcard in the same file, process them together
        """
        return self._process_combined_file(file, StatementCategory.creditcard)

    def process_bank(self, file: Path) -> ProcessedResult:
        """
        Richart has bank and creditcard in the same file, process them together
        """
        return self._process_combined_file(file, StatementCategory.bank)

    def _process_combined_file(self, file: Path, statement_type: StatementCategory) -> ProcessedResult:
        settings = self.get_settings(statement_type)

        # ensure the directory exists
        output_dir = Path(self.output_dir_format.format(source_name=type(
            self).source_name, statement_type=statement_type.value))
        os.makedirs(output_dir, exist_ok=True)

        with zipfile.ZipFile(file) as zipfp:
            filename = zipfp.namelist()[0]  # only contains one file
            with zipfp.open(filename, pwd=settings.password.encode()) as fp:
                # 0 for creditcard, 1 for bank
                if statement_type == StatementCategory.creditcard:
                    df = pd.read_excel(fp, sheet_name=0)
                elif statement_type == StatementCategory.bank:
                    df = pd.read_excel(fp, sheet_name=1)
                else:
                    return ProcessedResult(False, f"{statement_type} not supported by {type(self).source_name}")
        #print(df)
        df.iloc[:,0] = pd.to_datetime(df.iloc[:,0])
        df.iloc[:,1] = pd.to_datetime(df.iloc[:,1])
        years = df.iloc[:,0].dt.year.unique()
        months = df.iloc[:,0].dt.month.unique()
        for year in years:
            for month in months:
                result_df = df.loc[(df.iloc[:,0].dt.year == year) & (df.iloc[:,0].dt.month == month)]
                if result_df.empty:
                    continue

                output_file =  output_dir / f"{year}{str(month).zfill(2)}.csv"
                if output_file.exists():
                    if not self._should_replace(output_file, result_df):
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


