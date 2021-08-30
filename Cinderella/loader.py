import pandas as pd

import logging
from typing import Iterator, Union
from os import walk
from pathlib import Path

from parsers.base import StatementParser
from datatypes import Directives

LOGGER = logging.getLogger("StatementLoader")


class StatementLoader:

    def __init__(self, root: str, parsers: list):
        self.root = root
        self.categories = ["bank", "card", "receipt", "stock"]
        self.parsers = parsers

    def _find_parser(self, path: str) -> Union[StatementParser, None]:
        found = None
        for parser in self.parsers:
            if parser.identifier in path:
                found = parser
        return found

    def load(self) -> Iterator[Directives]:
        for category in self.categories:
            for (dirpath, _, filenames) in walk(Path(self.root, category)):
                for filename in filenames:
                    filepath = str(Path(dirpath, filename))
                    parser = self._find_parser(filepath)
                    if not parser:
                        LOGGER.warn("No parser found for file %s", filepath)
                        continue
                    LOGGER.info("File: %s, Identifier: %s", filepath, parser.identifier)
                    df = parser.read_statement(filepath)
                    directives = parser.parse(category, df)

                    yield directives

