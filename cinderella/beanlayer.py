import datetime
import logging
import re
from copy import deepcopy
from decimal import Decimal
from typing import Union, Any, Dict, Set, List

from beancount.loader import load_file
from beancount.parser import printer
from beancount.core.data import Transaction, Posting, filter_txns
from beancount.core.amount import Amount
from beancount.core.position import Cost
from beancount.core.position import CostSpec

from cinderella.configs import Configs
from cinderella.datatypes import Transactions

LOGGER = logging.getLogger("BeanCountAPI")


class BeanCountAPI:
    def __init__(self):
        self.config = Configs()

    def write_account_bean(self, accounts: list, output_path: str):

        accounts = sorted(list(set(accounts)))

        with open(output_path, "w") as f:
            for account in accounts:
                line = f"2020-01-01 open {account}\n"
                f.write(line)

    def write_bean(self, directives: Transactions, path: str):
        with open(path, "a") as f:
            for directive in directives:
                f.write(directive.to_bean())

    def _make_amount(self, amount: Decimal, currency: str):
        amount = amount.quantize(Decimal("1.00"))
        return Amount(amount, currency)

    def _make_simple_posting(self, account: str, price: Decimal, currency: str):
        amount = self._make_amount(price, currency)
        return self._make_posting(account, amount)

    def _make_posting(
        self,
        account: str,
        amount: Amount,
        cost: Union[Cost, CostSpec] = None,
        price: Amount = None,
        flag: str = None,
        meta: Dict[str, Any] = None,
    ):
        if not isinstance(account, str):
            LOGGER.error("account must be a string, got %s instead", account)
            raise RuntimeError
        if not meta:
            meta = dict()
        posting = Posting(account, amount, cost, price, flag, meta)
        return posting

    def _make_transaction(
        self,
        date: Union[datetime.datetime, datetime.date],
        title: str,
        postings: List[Posting],
        flag: str = "*",
        payee: str = None,
        meta: Dict[str, Any] = None,
        tags: Set = None,
        links: Set = None,
    ):
        if isinstance(date, datetime.datetime):
            date = date.date()

        if not meta:
            meta = dict()
        if not tags:
            tags = set()
        if not links:
            links = set()

        transaction = Transaction(meta, date, flag, payee, title, tags, links, postings)
        return transaction

    def _load_bean(self, path: str) -> list:
        entries, _, _ = load_file(path)
        return [transaction for transaction in filter_txns(entries)]

    def make_transaction(
        self,
        date: datetime.datetime,
        title: str,
        account: str,
        amount: Decimal,
        currency: str,
    ) -> Transaction:
        bean_amount = self._make_amount(amount, currency)
        posting = self._make_posting(account, bean_amount)

        return self._make_transaction(date, title, [posting])

    def add_transaction_comment(self, transaction: Transaction, value: str) -> None:
        count = len(transaction.meta.keys())
        key = f";{count+1}"

        transaction.meta[key] = value

    def add_posting_comment(
        self, transaction: Transaction, value: str, index: int = 0
    ) -> None:
        count = len(transaction.postings[index].meta.keys())
        key = f";{count+1}"

        if index < len(transaction.postings):
            if transaction.postings[index]:
                transaction.postings[index].meta[key] = value
            else:
                transaction.postings[index].meta = {key: value}

    def add_posting_amount(
        self, transaction: Transaction, number: Decimal, index: int = 0
    ) -> None:
        # https://github.com/beancount/beancount/blob/master/beancount/core/amount.py#L33
        posting = transaction.postings[index]
        old_amount = posting.units
        new_amount = self._make_amount(old_amount.number + number, old_amount.currency)
        posting = posting._replace(units=new_amount)  # replace namedtuple
        transaction.postings[index] = posting

    def add_transaction_posting(
        self, transaction: Transaction, posting: Posting
    ) -> int:
        transaction.postings.append(posting)
        # return index
        return len(transaction.postings) - 1

    def create_and_add_transaction_posting(
        self,
        transaction: Transaction,
        account: str,
        price: Decimal = None,
        currency: str = None,
    ) -> int:
        if not price or not currency:
            amount = None
        else:
            amount = self._make_amount(price, currency)
        posting = self._make_posting(account, amount)

        transaction.postings.append(posting)
        # return index
        return len(transaction.postings) - 1

    def print_beans(
        self, transactions: Transactions, filepath: str = None, mode: str = "a"
    ):
        if filepath:
            with open(filepath, mode) as f:
                printer.print_entries(transactions, file=f)
        else:
            printer.print_entries(transactions)

    def print_bean(self, transaction: Transaction):
        printer.print_entry(transaction)

    def find_keywords(self, transaction: Transaction, keywords: list[str]) -> bool:
        for keyword in keywords:
            found = self.find_keyword(transaction, keyword)
            if found:
                return True

        return False

    def find_keyword(self, transaction: Transaction, keyword: str) -> bool:
        # search transaction title
        regex = re.compile(keyword)
        if bool(re.search(regex, transaction.narration)):
            return True

        # search transaction meta
        for comment in transaction.meta.values():
            if bool(re.search(regex, comment)):
                return True

        # search postings meta
        for posting in transaction.postings:
            for comment in posting.meta.values():
                if bool(re.search(regex, comment)):
                    return True

        return False

    def merge_transactions(
        self, dest: Transaction, source: Transaction, keep_dest_accounts: bool
    ) -> Transaction:
        """
        merge source first posting to dest
        """
        dest_posting_comments = deepcopy(dest.postings[0].meta)
        source_posting_comments = deepcopy(source.postings[0].meta)
        source.postings[0].meta.clear()

        # clear and use new_entry
        if not keep_dest_accounts:
            dest.postings.clear()

        dest.postings.extend(source.postings)

        # restore and merge comments
        for comment in dest_posting_comments.values():
            self.add_posting_comment(dest, comment)
        for comment in source_posting_comments.values():
            self.add_posting_comment(dest, comment)

        for comment in source.meta.values():
            self.add_transaction_comment(dest, comment)
        return dest


if __name__ == "__main__":
    bc = BeanCountAPI()
    bc._load_bean("/Users/daniel/projects/Cinderella/beans/result.bean")
