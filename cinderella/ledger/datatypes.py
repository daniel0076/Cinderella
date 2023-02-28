from __future__ import annotations
from enum import Enum, auto
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any
from datetime import datetime
import hashlib
import re


class StatementType(Enum):
    invalid = "invalid"
    ignored = "ignored"
    custom = "custom"
    bank = "bank"
    creditcard = "creditcard"
    receipt = "receipt"
    stock = "stock"


class TransactionFlag(Enum):
    OK = auto()
    TRANSFER = auto()
    CONVERSIONS = auto()
    MERGED = auto()


class OnExistence(Enum):
    SKIP = auto()
    RENAME = auto()
    REPLACE = auto()
    CONCAT = auto()


@dataclass
class Amount:
    quantity: Decimal
    currency: str

    def __str__(self) -> str:
        return f"{self.quantity} {self.currency}"

    def __add__(self, other: Amount) -> Amount:
        if self.currency != other.currency:
            raise TypeError(f'Can not add "{other}" to "{self}", currency mismatch')
        return Amount(self.quantity + other.quantity, self.currency)

    def __iadd__(self, other: Amount) -> Amount:
        if self.currency != other.currency:
            raise TypeError(f'Can not add "{other}" to "{self}", currency mismatch')

        self.quantity += other.quantity
        return self

    def __hash__(self):
        return hash((self.quantity, self.currency))


@dataclass
class Posting:
    account: str
    amount: Amount
    meta: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create_simple(cls, account: str, quantity: Decimal, currency: str):
        posting = Posting(account, Amount(quantity, currency))
        return posting


@dataclass
class Transaction:
    datetime_: datetime
    title: str
    postings: list[Posting] = field(default_factory=list)
    meta: dict[str, Any] = field(default_factory=dict)
    flag: TransactionFlag = TransactionFlag.OK

    @classmethod
    def create_simple(
        cls, datetime_: datetime, title: str, account, quantity, currency
    ):
        txn = Transaction(datetime_, title)
        txn.append_postings(Posting.create_simple(account, quantity, currency))
        return txn

    def create_and_append_posting(self, account: str, quantity: Decimal, currency: str):
        self.postings.append(Posting(account, Amount(quantity, currency)))

    def append_postings(self, *postings: Posting):
        for posting in postings:
            self.postings.append(posting)

    def add_posting_amount(self, index: int, quantity: Decimal, currency: str):
        try:
            self.postings[index].amount += Amount(quantity, currency)
        except TypeError as err:
            print(err)

    def insert_comment(
        self, key: str, value: Any, comment_exists: OnExistence = OnExistence.REPLACE
    ):
        if self.meta.get(key, None):
            if comment_exists == OnExistence.SKIP:
                return
            elif comment_exists == OnExistence.RENAME:
                key_hash = hashlib.sha256(key.encode()).hexdigest()[:5]
                self.meta[key_hash] = value
            elif comment_exists == OnExistence.CONCAT:
                self.meta[key] += value
            else:
                self.meta[key] = value
        return

    def merge(
        self, source: Transaction, comment_exists: OnExistence, merge_postings: bool
    ):
        # merge/replace comments
        for key, value in source.meta.items():
            print(key, value)
            self.insert_comment(key, value, comment_exists)

        if merge_postings:
            self.postings.extend(source.postings)

    def grep(self, keyword: str) -> bool:
        if re.search(keyword, self.title):
            return True

        # search transaction meta
        for comment in self.meta.values():
            if re.search(keyword, comment):
                return True

        return False


@dataclass
class Ledger:
    source: str
    typ: StatementType
    transactions: list[Transaction] = field(default_factory=list)

    def __str__(self) -> str:
        return f"=== Ledger source: {self.source}, type: {self.typ} ===\n{self.transactions}"

    def __len__(self) -> int:
        return len(self.transactions)

    def __add__(self, other: Ledger) -> Ledger:
        if self.typ != other.typ or self.source != other.source:
            raise TypeError(
                f'Can not add "{other}" to "{self}", type or source mismatch'
            )
        return Ledger(self.source, self.typ, self.transactions + other.transactions)

    def __iadd__(self, other: Ledger) -> Ledger:
        if self.typ != other.typ or self.source != other.source:
            raise TypeError(
                f'Can not add "{other}" to "{self}", type or source mismatch'
            )
        self.transactions.extend(other.transactions)
        return self

    def sort(self):
        pass

    def create_and_append_txn(
        self, date, title, account, quantity, currency
    ) -> Transaction:
        txn = Transaction(date, title)
        txn.create_and_append_posting(account, quantity, currency)
        self.transactions.append(txn)
        return txn

    def append_txn(self, txn: Transaction):
        self.transactions.append(txn)
