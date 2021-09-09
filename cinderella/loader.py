import logging
from typing import Iterator, Union
from os import walk, getcwd
from pathlib import Path
from collections import defaultdict

from cinderella.parsers.base import StatementParser
from cinderella.datatypes import Transactions, StatementCategory
from cinderella.beanlayer import BeanCountAPI
from cinderella.configs import Configs

LOGGER = logging.getLogger("StatementLoader")
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
        self.bean_loader = BeanLoader()

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
                transactions = parser.parse(category, filepath)

                yield transactions

    def _dedup_transactions(
        self,
        lhs: Union[Transactions, list[Transactions]],
        rhs: Union[Transactions, list[Transactions]] = None,
    ):
        if isinstance(rhs, Transactions):
            rhs = [rhs]
        if isinstance(lhs, Transactions):
            lhs = [lhs]

        bucket = set()

        for transactions in lhs:
            unique = []
            for transaction in transactions:
                key = (
                    transaction.date,
                    str(transaction.postings[0].units),
                    transaction.narration,
                )
                if key not in bucket:
                    unique.append(transaction)
                    bucket.add(key)

            transactions.clear()
            transactions.extend(unique)

        if not rhs:
            return

        for transactions in rhs:
            unique = []
            for transaction in transactions:
                key = (
                    transaction.date,
                    str(transaction.postings[0].units),
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
                existing_trans.extend(trans)

        # flatten and dedup the dict
        category_transactions = defaultdict(list)
        for category, trans_dict in category_trans_map.items():
            for trans in trans_dict.values():
                assert isinstance(trans, Transactions)
                self._dedup_transactions(trans)
                category_transactions[category].append(trans)

        # merge similar transactions, like a transaction may appear in creditcard and receipt
        receipt_trans_list = category_transactions.pop(StatementCategory.receipt, [])
        for category, trans_list in category_transactions.items():
            self._merge_similar_transactions(receipt_trans_list, trans_list)
        category_transactions[StatementCategory.receipt] = receipt_trans_list

        # dedup transactions listed in custom bean files
        custom_transactions = self.bean_loader.load_custom_bean()
        autogen_transactions_list = []
        for trans_list in category_transactions.values():
            autogen_transactions_list.extend(trans_list)

        self._dedup_transactions(custom_transactions, autogen_transactions_list)

        return category_transactions


class BeanLoader:
    def __init__(self):
        self.configs = Configs()
        self.beancount_api = BeanCountAPI()
        self.default_path = str(Path(CURRENT_DIR, self.configs.default_output))

    def load_custom_bean(self, root: str = None) -> Transactions:
        if not root:
            root = self.default_path

        category = StatementCategory.custom
        transactions = Transactions(category, category.name)

        keyword = self.configs.custom_bean_keyword
        for (dirpath, _, filenames) in walk(root):
            for filename in filenames:
                path = str(Path(dirpath, filename))
                if keyword not in path or not filename.endswith("bean"):
                    continue

                entries = self._load_bean(path)
                transactions.extend(entries)

        return transactions

    def _load_bean(self, path) -> list:
        results = self.beancount_api._load_bean(path)

        return results
