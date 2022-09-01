import camelot
import pandas as pd
from settings import SourceSettings, StatementSettings
from base import ProcessorBase, ProcessedResult
from datatypes import StatementCategory
from pathlib import Path
from datetime import datetime


class KokoPDFProcessor(ProcessorBase):
    identifier = "koko"  # class static variable

    def __init__(self, settings: SourceSettings):
        super().__init__(settings)

    def _process_creditcard(self, filename: str, settings: StatementSettings) -> ProcessedResult:
        # no lattices, edge_tol used to rule out small tables
        tables = camelot.read_pdf(
            filename,
            password=settings.password,
            flavor="stream",
            pages="1-end",
            split_text=True,
            edge_tol=100,
            row_tol=10,
        )

        # last 3 tables are not about statement info
        frames = [table.df for table in tables[0:-3]]
        table = pd.concat(frames)
        table.reset_index(drop=True, inplace=True)

        # the first table contains headers, drop the beginning unwanted 4 rows
        # don't need them anymore, use inplace
        table.drop(axis=0, index=[0, 1, 2, 3, 4], inplace=True)
        table.reset_index(drop=True, inplace=True)

        # merge the errorly-cut rows to previous row
        drop_rows = []
        for index, row in table.iterrows():
            if row.iat[0] == "":
                missing_text = row.iat[2]
                table.iat[index - 1, 2] += missing_text
                drop_rows.append(index)

        table.drop(drop_rows, inplace=True)  # don't need them anymore, use inplace
        table.reset_index(drop=True, inplace=True)

        #  post processing the price column
        table[3] = table[3].str.replace(",", "")

        # try to retrieve statement date from the filename (easier)
        try:
            taiwanese_date = Path(filename).stem.split("_")[-1]
            year = int(taiwanese_date[0:-2])+1911
            month = int(taiwanese_date[-2:])
            statement_date = datetime(year=year, month=month, day=1)
        except ValueError:
            statement_date = datetime.now().date()

        result = ProcessedResult(True, StatementCategory.creditcard, table, statement_date)
        return result
