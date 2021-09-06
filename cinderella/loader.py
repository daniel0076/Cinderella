import logging
from typing import Iterator, Union
from os import walk
from pathlib import Path
from collections import defaultdict

from cinderella.parsers.base import StatementParser
from cinderella.datatypes import Transactions

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

    def _load_file(self) -> Iterator[Transactions]:
        for (dirpath, _, filenames) in walk(self.root):
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

                LOGGER.info(
                    "File: %s, Category: %s, Parser: %s",
                    filepath,
                    category,
                    parser.identifier,
                )
                directives = parser.parse(category, filepath)

                yield directives

    def _dedup_transaction(self, transactions: Transactions) -> Transactions:
        bucket = set()
        unique = Transactions(transactions.category, transactions.source)
        for transaction in transactions:
            key = (transaction.date, transaction.postings[0].units, transaction.narration)
            if key not in bucket:
                unique.append(transaction)
                bucket.add(key)
        return unique

    def load(self) -> dict[str, list[Transactions]]:
        category_trans_map = dict()
        for category in self.categories:
            category_trans_map[category] = {}

        for trans in self._load_file():
            existing_trans = category_trans_map[trans.category].get(trans.source, None)
            if not existing_trans:
                category_trans_map[trans.category][trans.source] = trans
            else:
                existing_trans += trans

        # flatten and dedup the dict
        category_transactions = defaultdict(list)
        for category, trans_dict in category_trans_map.items():
            for trans in trans_dict.values():
                category_transactions[category].append(self._dedup_transaction(trans))

        return category_transactions
