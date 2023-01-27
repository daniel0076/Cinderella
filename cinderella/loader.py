import logging
from typing import Iterator, Union
from os import walk, getcwd
from pathlib import Path
from collections import defaultdict

from cinderella.parsers.base import StatementParser
from cinderella.datatypes import Transactions, StatementCategory
from cinderella.beanlayer import BeanCountAPI
from cinderella.settings import CinderellaSettings

LOGGER = logging.getLogger(__name__)
CURRENT_DIR = getcwd()


class StatementLoader:
    def __init__(self, root: str, parsers: list):
        self.root = root
        self.categories = [
            category
            for category in StatementCategory
            if category != StatementCategory.custom
        ]
        self.parsers = parsers
        self.beancount_api = BeanCountAPI()

    def _find_parser(self, path: str) -> Union[StatementParser, None]:
        found = None
        for parser in self.parsers:
            if parser.identifier in path:
                found = parser
        return found

    def _find_category(self, path: str) -> Union[StatementCategory, None]:
        for category in self.categories:
            if category.name in path:
                return category
        return None

    def _load_file(self) -> Iterator[Transactions]:
        LOGGER.debug("Loading statement files")
        for dirpath, _, filenames in walk(self.root):
            LOGGER.debug(f"Current directory: {dirpath}")
            for filename in filenames:
                if filename.startswith("."):
                    continue
                filepath = str(Path(dirpath, filename))
                parser = self._find_parser(filepath)
                category = self._find_category(filepath)

                if not parser or not category:
                    LOGGER.warn(
                        "Load fail: %s, Category: %s, Parser: %s",
                        filepath,
                        "Unknown" if not category else category,
                        getattr(parser, "identifier", "Unknown"),
                    )
                    continue

                LOGGER.debug(
                    f"File: {filename}, Category: {category}, Parser: {parser.identifier}"
                )
                transactions = parser.parse(category, filepath)

                yield transactions

    def load(self) -> dict[StatementCategory, list[Transactions]]:
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
        self.default_path = str(
            Path(CURRENT_DIR, self.settings.beancount_settings.output_beanfiles_folder))

    def load_custom_bean(self, root: str = "") -> Transactions:
        if not root:
            root = self.default_path

        category = StatementCategory.custom
        transactions = Transactions(category, category.name)

        keyword = self.settings.custom_bean_keyword
        LOGGER.debug("===Loading custom bean files===")
        for dirpath, _, filenames in walk(root):
            LOGGER.debug(f"Current directory {dirpath}")
            for filename in filenames:
                path = str(Path(dirpath, filename))
                if keyword not in path or not filename.endswith("bean"):
                    continue
                LOGGER.debug(f"Bean file: {filename}")

                entries = self._load_bean(path)
                transactions.extend(entries)

        return transactions

    # TODO: merge load_XXX_bean
    def load_ignored_bean(self, root: str = None) -> Transactions:
        if not root:
            root = self.default_path

        category = StatementCategory.ignored
        transactions = Transactions(category, category.name)

        keyword = self.settings.ignored_bean_keyword
        LOGGER.debug("===Loading ignored bean files===")
        for dirpath, _, filenames in walk(root):
            LOGGER.debug(f"Current directory {dirpath}")
            for filename in filenames:
                path = str(Path(dirpath, filename))
                if keyword not in path or not filename.endswith("bean"):
                    continue
                LOGGER.debug(f"Bean file: {filename}")

                entries = self._load_bean(path)
                transactions.extend(entries)

        return transactions

    def _load_bean(self, path) -> list:
        results = self.beancount_api._load_bean(path)

        return results
