import logging
from typing import Iterator, Union
from os import walk, getcwd
from pathlib import Path
from collections import defaultdict

from cinderella.parsers.base import StatementParser
from cinderella.datatypes import Transactions, StatementType
from cinderella.beanlayer import BeanCountAPI
from cinderella.settings import CinderellaSettings, LOG_NAME

logger = logging.getLogger(LOG_NAME)
CURRENT_DIR = getcwd()


class StatementLoader:
    def __init__(self, root: str, parsers: list):
        self.root = root
        self.categories = [
            category for category in StatementType if category != StatementType.custom
        ]
        self.parsers = parsers
        self.beancount_api = BeanCountAPI()

    def _find_parser(self, path: str) -> Union[StatementParser, None]:
        found = None
        for parser in self.parsers:
            if parser.identifier in path:
                found = parser
        return found

    def _find_category(self, path: str) -> Union[StatementType, None]:
        for category in self.categories:
            if category.name in path:
                return category
        return None

    def _load_file(self) -> Iterator[Transactions]:
        logger.debug("Loading statement files")
        for dirpath, _, filenames in walk(self.root):
            logger.debug(f"Current directory: {dirpath}")
            for filename in filenames:
                if filename.startswith("."):
                    continue
                filepath = str(Path(dirpath, filename))
                parser = self._find_parser(filepath)
                category = self._find_category(filepath)

                if not parser or not category:
                    logger.warn(
                        "Load fail: %s, Category: %s, Parser: %s",
                        filepath,
                        "Unknown" if not category else category,
                        getattr(parser, "identifier", "Unknown"),
                    )
                    continue

                logger.debug(
                    f"File: {filename}, Category: {category}, Parser: {parser.identifier}"
                )
                transactions = parser.parse(category, filepath)

                yield transactions

    def load(self) -> dict[StatementType, list[Transactions]]:
        category_trans_map = dict()
        for category in self.categories:
            category_trans_map[category] = {}

        for trans in self._load_file():
            existing_trans = category_trans_map[trans.category].get(trans.source, None)
            if not existing_trans:
                category_trans_map[trans.category][trans.source] = trans
            else:
                existing_trans.extend(trans)

        # flatten the dict
        category_transactions = defaultdict(list)
        for category, trans_dict in category_trans_map.items():
            for trans in trans_dict.values():
                category_transactions[category].append(trans)

        return category_transactions


class BeanLoader:
    def __init__(self, settings: CinderellaSettings):
        self.settings = settings
        self.beancount_api = BeanCountAPI()

    def load_beanfile_as_transactions(
        self, path: Path | str, category: StatementType
    ) -> Transactions:
        transactions = Transactions(category, category.name)
        logger.debug(f"===Loading beanfiles: {category.name}===")
        for dirpath, _, filenames in walk(path):
            logger.debug(f"Current directory {dirpath}")
            for filename in filenames:
                path = Path(dirpath, filename)
                logger.debug(f"Loading beanfile: {filename}")

                entries = self.beancount_api._load_bean(path.as_posix())
                transactions.extend(entries)

        return transactions
