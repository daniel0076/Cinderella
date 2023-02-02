import os
import pandas as pd
import logging
import zipfile
from pathlib import Path

from cinderella.preprocessors.base import ProcessorBase, ProcessedResult
from cinderella.datatypes import AfterProcessedAction, StatementType
from cinderella.settings import LOG_NAME, RawStatementProcessSettings

logger = logging.getLogger(LOG_NAME)


class Richart(ProcessorBase):
    source_name = "richart"

    def process(self, file: Path) -> ProcessedResult:
        """
        Overrides the default process
        Richart has bank and creditcard in the same file, process them together
        """
        supported_types = [StatementType.bank, StatementType.creditcard]
        all_success = True
        for statement_type in supported_types:
            settings = self.settings_by_type.get(
                statement_type,
                RawStatementProcessSettings(
                    statement_type, "", AfterProcessedAction.move
                ),
            )
            result = self._process_combined_file(file, settings)
            if not result.success:
                all_success = False
                logger.error(result.message)

        if all_success:
            # Richart has bank and creditcard in the same file, process them together
            self.post_process(file, StatementType.bank)

        return ProcessedResult(True, "")  # Supress warning outside

    def process_receipt(
        self, file: Path, settings: RawStatementProcessSettings
    ) -> ProcessedResult:
        return ProcessedResult(False, f"{file} not supported by {self.source_name}")

    def process_creditcard(
        self, file: Path, settings: RawStatementProcessSettings
    ) -> ProcessedResult:
        """
        Richart has bank and creditcard in the same file, process them together
        """
        return self._process_combined_file(file, settings)

    def process_bank(
        self, file: Path, settings: RawStatementProcessSettings
    ) -> ProcessedResult:
        """
        Richart has bank and creditcard in the same file, process them together
        """
        return self._process_combined_file(file, settings)

    def _process_combined_file(
        self, file: Path, settings: RawStatementProcessSettings
    ) -> ProcessedResult:
        # ensure the directory exists
        output_dir = Path(
            self.output_dir, StatementType.receipt.value, type(self).source_name
        )
        os.makedirs(output_dir, exist_ok=True)

        with zipfile.ZipFile(file) as zipfp:
            filename = zipfp.namelist()[0]  # only contains one file
            with zipfp.open(filename, pwd=settings.password.encode()) as fp:
                # 0 for creditcard, 1 for bank
                if settings.statement_type == StatementType.creditcard:
                    df = pd.read_excel(fp, sheet_name=0)
                elif settings.statement_type == StatementType.bank:
                    df = pd.read_excel(fp, sheet_name=1)
                else:
                    return ProcessedResult(
                        False,
                        f"{settings.statement_type} not supported by {type(self).source_name}",
                    )

        df.iloc[:, 0] = pd.to_datetime(df.iloc[:, 0])
        df.iloc[:, 1] = pd.to_datetime(df.iloc[:, 1])
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
                        logger.warning(f"Replace {output_file} with newer records")

                print(f"output {output_file}")
                result_df.to_csv(output_file, index=False)

        return ProcessedResult(True, "")

    def _should_replace(self, target: Path, result_df: pd.DataFrame):
        existing_df = pd.read_csv(target)
        if len(existing_df) < len(result_df):
            return True

        return False
