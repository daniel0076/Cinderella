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

    def _find_category(self, path: str) -> Union[str, None]:
        for category in self.categories:
            if category in path:
                return category
        return None

    def load(self) -> Iterator[Directives]:
        for (dirpath, _, filenames) in walk(self.root):
            for filename in filenames:
                if filename.startswith("."):
                    continue
                filepath = str(Path(dirpath, filename))
                parser = self._find_parser(filepath)
                category = self._find_category(filepath)

                if not parser or not category:
                    LOGGER.warn("Load fail: %s, Category: %s, Parser: %s",
                                filepath,
                                "Unknown" if not category else category,
                                getattr(parser, "identifier", "Unknown"))
                    continue

                LOGGER.info("File: %s, Category: %s, Parser: %s", filepath, category, parser.identifier)
                df = parser.read_statement(filepath)
                directives = parser.parse(category, df)

                yield directives

