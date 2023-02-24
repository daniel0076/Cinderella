import os
import pandas as pd
import logging
import zipfile
from pathlib import Path

from cinderella.statement.preprocessors.base import ProcessorBase, ProcessedResult
from cinderella.statement.datatypes import AfterProcessedAction
from cinderella.ledger.datatypes import StatementType
from cinderella.settings import LOG_NAME, RawStatementProcessSettings

logger = logging.getLogger(LOG_NAME)


class Richart(ProcessorBase):
    source_name = "richart"

    def process(self, file: Path) -> ProcessedResult:
        """
        Richart has bank and creditcard in the same file
        Overrides the default process
        """
        default_settings = RawStatementProcessSettings(
            StatementType.bank, "", AfterProcessedAction.move
        )
        settings = self.settings_by_type.get(StatementType.bank, None)
        if not settings:
            settings = self.settings_by_type.get(
                StatementType.creditcard, default_settings
            )

        if not zipfile.is_zipfile(file):
            return ProcessedResult(False, f"{file} is not a valid zip file")

        with zipfile.ZipFile(file) as zipfp:
            filename = zipfp.namelist()[0]  # only contains one file
            with zipfp.open(filename, pwd=settings.password.encode()) as fp:
                # 0 for creditcard, 1 for bank
                creditcard_df = pd.read_excel(fp, sheet_name=0)
                bank_df = pd.read_excel(fp, sheet_name=1)

        bank_result = self._split_by_year_month(bank_df, StatementType.bank)
        creditcard_result = self._split_by_year_month(
            creditcard_df, StatementType.creditcard
        )

        if bank_result.success and creditcard_result.success:
            self.post_process(file, settings)
            return ProcessedResult(True, "")  # Supress warning outside

        if not bank_result.success:
            logger.error(bank_result.message)
        if not creditcard_result.success:
            logger.error(creditcard_result.message)

        # Supress warning outside
        return ProcessedResult(False, f"{self.source_name} preprocess failed")

    def process_receipt(
        self, file: Path, settings: RawStatementProcessSettings
    ) -> ProcessedResult:
        raise NotImplementedError

    def process_creditcard(
        self, file: Path, settings: RawStatementProcessSettings
    ) -> ProcessedResult:
        raise NotImplementedError

    def process_bank(
        self, file: Path, settings: RawStatementProcessSettings
    ) -> ProcessedResult:
        raise NotImplementedError

    def _split_by_year_month(
        self, df: pd.DataFrame, statement_type: StatementType
    ) -> ProcessedResult:
        # ensure the directory exists
        output_dir = Path(self.output_dir, statement_type.value, type(self).source_name)
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

                print(f"preprocessor[{self.source_name}]: output to {output_file}")
                result_df.to_csv(output_file, index=False)

        return ProcessedResult(True, "")

    def _should_replace(self, target: Path, result_df: pd.DataFrame):
        existing_df = pd.read_csv(target)
        if len(existing_df) < len(result_df):
            return True

        return False
