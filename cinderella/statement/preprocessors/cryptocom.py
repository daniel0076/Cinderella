import os
import pandas as pd
from pathlib import Path
from . import utils

from cinderella.ledger.datatypes import StatementType
from cinderella.settings import RawStatementProcessSettings
from cinderella.statement.preprocessors.base import ProcessorBase, ProcessedResult


class CryptoCom(ProcessorBase):
    source_name = "cryptocom"

    def process_creditcard(
        self, file: Path, settings: RawStatementProcessSettings
    ) -> ProcessedResult:
        # ensure the directory exists
        output_dir = Path(
            self.output_dir, StatementType.creditcard.value, type(self).source_name
        )
        os.makedirs(output_dir, exist_ok=True)

        df = pd.read_csv(file, sep=",")
        for year, month, result_df in utils.split_by_year_month(df, 0):
            output_file = output_dir / f"{year}{str(month).zfill(2)}.csv"
            if output_file.exists():
                result_df = utils.merge_dataframe(output_file, result_df)

            if result_df is not None:
                result_df.to_csv(output_file, index=False)

        return ProcessedResult(True, "")  # Supress warning outside

    def process_receipt(self, _, __) -> ProcessedResult:
        raise NotImplementedError

    def process_bank(self, _, __) -> ProcessedResult:
        raise NotImplementedError
