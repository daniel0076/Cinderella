import logging
from typing import Iterator, Union
from os import walk
from pathlib import Path
from collections import defaultdict

from cinderella.parsers.base import StatementParser
from cinderella.datatypes import Transactions, StatementCategory
from cinderella.beanlayer import BeanCountAPI

LOGGER = logging.getLogger("StatementLoader")


class StatementLoader:
    def __init__(self, root: str, parsers: list):
        self.root = root
        self.categories = list(StatementCategory)
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

    def _dedup_transactions(self, transactions: Transactions):
        bucket = set()
        unique = []
        for transaction in transactions:
            key = (
                transaction.date,
                str(transaction.postings[0]),
                transaction.narration,
            )
            if key not in bucket:
                unique.append(transaction)
                bucket.add(key)

        transactions.clear()
        transactions.extend(unique)

    def _merge_similar_transactions(
        self, lhs: Union[Transactions, list], rhs: Union[Transactions, list]
    ) -> None:
        """
        merge similar transactions from rhs to lhs
        two transactions are deemed similar if they have common date and amount
        """
        if isinstance(rhs, Transactions):
            rhs = [rhs]
        if isinstance(lhs, Transactions):
            lhs = [lhs]

        # build map for comparison
        bucket: dict[tuple, list] = defaultdict(list)
        counter: dict[tuple, int] = dict()
        for trans_list in lhs:
            for trans in trans_list:
                key = (trans.date, str(trans.postings[0].units))
                if key in bucket.keys():
                    counter[key] += 1
                    bucket[key].append(trans)
                else:
                    counter[key] = 1
                    bucket[key].append(trans)

        for trans_list in rhs:
            unique = []
            for trans in trans_list:
                key = (trans.date, str(trans.postings[0].units))
                count = counter.get(key, 0)
                if count > 0:
                    counter[key] -= 1
                    index = counter[key]
                    existing_trans = bucket[key][index]
                    self.beancount_api.merge_transactions(
                        existing_trans, trans, keep_dest_accounts=False
                    )
                else:
                    unique.append(trans)
            trans_list.clear()
            trans_list.extend(unique)

    def load(self) -> dict[StatementCategory, list[Transactions]]:
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
        category_transactions: dict[
            StatementCategory, list[Transactions]
        ] = defaultdict(list)
        for category, trans_dict in category_trans_map.items():
            for trans in trans_dict.values():
                self._dedup_transactions(trans)
                category_transactions[category].append(trans)

        # merge similar transactions, like a transaction may appear in creditcard and receipt
        receipt_trans_list = category_transactions.pop(StatementCategory.receipt, [])
        for category, trans_list in category_transactions.items():
            self._merge_similar_transactions(receipt_trans_list, trans_list)

        category_transactions[StatementCategory.receipt] = receipt_trans_list

        return category_transactions
