from collections.abc import Iterable
from pathlib import Path
from typing import Optional, Tuple
import pandas as pd
import os


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


def move_to_folder(
    src: Path,
    dst: Path,
):
    """
    Move all files in input_dir to output_dir

    :param src: Description
    :type src: Path
    :param dst: Description
    :type dst: Path
    """
    if not src.exists():
        raise FileNotFoundError(f"{src} does not exist or is not a directory.")

    if dst.exists() and not dst.is_dir():
        raise NotADirectoryError(f"{dst} is not a directory.")

    # create dst folder
    os.makedirs(dst, exist_ok=True)

    # if src is file, move it directly
    if src.is_file():
        dst_file = dst / src.name
        if dst_file.exists():
            raise FileExistsError(f"{dst_file} already exists.")
        os.rename(src, dst_file)
        return

    # move all files in src to dst
    for file in src.iterdir():
        if not file.is_file():
            continue
        dst = dst / file.name
        # check if dst exists
        if dst.exists():
            raise FileExistsError(f"{dst} already exists.")
        os.rename(file, dst)
