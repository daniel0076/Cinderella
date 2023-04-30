from collections.abc import Iterable
from pathlib import Path
from typing import Optional, Tuple
import pandas as pd


def split_by_year_month(
    df: pd.DataFrame, date_idx: int
) -> Iterable[Tuple[int, int, pd.DataFrame]]:
    # convert column[date_idx] to datetime
    df[df.columns[date_idx]] = pd.to_datetime(df.iloc[:, date_idx])
    years = df.iloc[:, date_idx].dt.year.unique()
    months = df.iloc[:, date_idx].dt.month.unique()
    for year in years:
        for month in months:
            result_df = df.loc[
                (df.iloc[:, 0].dt.year == year) & (df.iloc[:, 0].dt.month == month)
            ]
            if result_df.empty:
                continue
            yield year, month, result_df


def merge_dataframe(existing_file: Path, df: pd.DataFrame) -> Optional[pd.DataFrame]:
    existing_df = pd.read_csv(existing_file).astype(str)
    df = df.astype(str)
    # union the two dataframes
    existing_df = pd.concat([existing_df, df], ignore_index=True).drop_duplicates()
    return existing_df
