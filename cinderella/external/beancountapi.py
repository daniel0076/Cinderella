from __future__ import annotations
import datetime
import logging
import re
from copy import deepcopy
from decimal import Decimal
from typing import Union, Any, Dict, Set, List, Optional
from pathlib import Path

from beancount.loader import load_file
from beancount.parser import printer
from beancount.core.data import Transaction as BeanTransaction, Posting, filter_txns
from beancount.core.amount import Amount
from beancount.core.position import Cost
from beancount.core.position import CostSpec

from cinderella.utils import iterate_files
from cinderella.ledger.datatypes import (
    Ledger,
    Transaction as InternalTransaction,
    StatementType,
)
from cinderella.settings import LOG_NAME

logger = logging.getLogger(LOG_NAME)


class BeanCountAPI:
    def __init__(self):
        pass

    def write_accounts_to_beanfile(self, accounts: list, output_path: str):
        accounts = sorted(list(set(accounts)))

        path = Path(output_path)
        path.parent.mkdir(exist_ok=True, parents=True)
        with open(output_path, "w") as f:
            for account in accounts:
                line = f"2020-01-01 open {account}\n"
                f.write(line)

    def write_bean(self, directives: Ledger, output_path: str):
        path = Path(output_path)
        path.parent.mkdir(exist_ok=True, parents=True)
        with open(path, "a") as f:
            for directive in directives:
                f.write(directive.to_bean())

    def make_amount(self, amount: Decimal, currency: str) -> Amount:
        amount = amount.quantize(Decimal("1.0000"))
        return Amount(amount, currency)

    def make_cost(
        self,
        number: Decimal,
        currency: str,
        date: datetime.date,
        label: Optional[str] = None,
    ) -> Cost:
        return Cost(number, currency, date, label)

    def make_simple_posting(self, account: str, price: Decimal, currency: str):
        amount = self.make_amount(price, currency)
        return self.make_posting(account, amount)

    def make_posting(
        self,
        account: str,
        amount: Union[Amount, None],
        cost: Union[Cost, CostSpec] = None,
        price: Amount = None,
        flag: str = None,
        meta: Dict[str, Any] = None,
    ):
        if not isinstance(account, str):
            logger.error("account must be a string, got %s instead", account)
            raise RuntimeError
        if not meta:
            meta = dict()
        posting = Posting(account, amount, cost, price, flag, meta)
        return posting

    def make_transaction(
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

        transaction = BeanTransaction(
            meta, date, flag, payee, title, tags, links, postings
        )
        return transaction

    def load_beanfile_to_internal_transactions(
        self, path: Union[Path, str]
    ) -> list[InternalTransaction]:
        if isinstance(path, str):
            if not path:
                return []
            path = Path(path)

        transactions = []
        logger.debug(f"===Loading beanfiles: {path.as_posix()}===")
        for file in iterate_files(path):
            entries, _, _ = load_file(file.as_posix())
            transactions.extend(filter_txns(entries))

        return self.convert_to_internal_transactions(transactions)

    def convert_to_internal_transactions(
        self, transactions: list[BeanTransaction]
    ) -> list[InternalTransaction]:
        result = []

        for bean_txn in transactions:
            c_txn = InternalTransaction(bean_txn.date, bean_txn.narration)
            for posting in bean_txn.postings:
                c_txn.create_and_append_posting(
                    posting.account, posting.units.number, posting.units.currency
                )
            result.append(c_txn)

        return result

    def make_simple_transaction(
        self,
        date: datetime.datetime,
        title: str,
        account: str,
        amount: Decimal,
        currency: str,
    ) -> BeanTransaction:
        bean_amount = self.make_amount(amount, currency)
        posting = self.make_posting(account, bean_amount)

        return self.make_transaction(date, title, [posting])

    def add_transaction_comment(self, transaction: BeanTransaction, value: str) -> None:
        count = len(transaction.meta.keys())
        key = f";{count+1}"

        transaction.meta[key] = value

    def add_posting_comment(
        self, transaction: BeanTransaction, value: str, index: int = 0
    ) -> None:
        count = len(transaction.postings[index].meta.keys())
        key = f";{count+1}"

        if index < len(transaction.postings):
            if transaction.postings[index]:
                transaction.postings[index].meta[key] = value
            else:
                transaction.postings[index].meta = {key: value}

    def add_posting_amount(
        self, transaction: BeanTransaction, number: Decimal, index: int = 0
    ) -> None:
        # https://github.com/beancount/beancount/blob/master/beancount/core/amount.py#L33
        posting = transaction.postings[index]
        old_amount = posting.units
        new_amount = self.make_amount(old_amount.number + number, old_amount.currency)
        posting = posting._replace(units=new_amount)  # replace namedtuple
        transaction.postings[index] = posting

    def add_transaction_posting(
        self, transaction: BeanTransaction, posting: Posting
    ) -> int:
        transaction.postings.append(posting)
        # return index
        return len(transaction.postings) - 1

    def create_and_add_transaction_posting(
        self,
        transaction: BeanTransaction,
        account: str,
        price: Decimal = None,
        currency: str = None,
    ) -> int:
        if not price or not currency:
            amount = None
        else:
            amount = self.make_amount(price, currency)
        posting = self.make_posting(account, amount)

        transaction.postings.append(posting)
        # return index
        return len(transaction.postings) - 1

    def print_beans(self, Ledger: Ledger, filepath: str = None, mode: str = "a"):
        if filepath:
            with open(filepath, mode) as f:
                printer.print_entries(Ledger, file=f)
        else:
            printer.print_entries(Ledger)

    def print_bean(self, transaction: BeanTransaction):
        printer.print_entry(transaction)

    def find_keywords(self, transaction: BeanTransaction, keywords: list[str]) -> bool:
        for keyword in keywords:
            found = self.find_keyword(transaction, keyword)
            if found:
                return True

        return False

    def find_keyword(self, transaction: BeanTransaction, keyword: str) -> bool:
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

    def merge_Ledger(
        self, dest: BeanTransaction, source: BeanTransaction, keep_dest_accounts: bool
    ) -> BeanTransaction:
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


def make_statement_accounts(statement_types: list[StatementType], display_name: str):
    common_prefix = {
        StatementType.bank: "Assets:Bank:",
        StatementType.creditcard: "Liabilities:CreditCard:",
        StatementType.receipt: "Assets:Cash:",
    }

    result = {}
    for typ in statement_types:
        if not common_prefix.get(typ, None):
            continue
        result[typ] = common_prefix[typ] + display_name

    return result


if __name__ == "__main__":
    bc = BeanCountAPI()
    bc._load_bean("/Users/daniel/projects/Cinderella/beans/result.bean")
