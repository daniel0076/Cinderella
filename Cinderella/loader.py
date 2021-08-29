import pandas as pd
import logging
from typing import Iterator
from os import listdir
from os.path import isfile
from pathlib import Path

from datatypes import Statement

LOGGER = logging.getLogger("StatementLoader")


class StatementLoader:

    def __init__(self, root: str):
        self.root = root
        self.categories = ["bank", "card", "receipt", "stock"]
        self.files = {}

        for category in self.categories:
            path = Path(root, category)
            self.files[category] = [Path(path, f) for f in listdir(path) if isfile(Path(path, f))]

    def load_statements(self) -> Iterator[Statement]:
        for category, files in self.files.items():
            for filepath in files:
                if filepath.suffix == ".csv":
                    records = []
                    with open(filepath) as f:
                        for line in f:
                            line = line.rstrip()
                            if not line:
                                continue
                            records.append(line)

                elif filepath.suffix == ".xlsx" or filepath.suffix == ".xls":
                    try:
                        df = pd.read_excel(filepath)
                    except:
                        LOGGER.error("Failed to load statements %s with pandas excel", filepath)
                        continue
                    records = df.values.tolist()
                else:
                    LOGGER.error("Failed to load statements from %s", filepath)
                    continue

                yield Statement(category, filepath.name, records)
