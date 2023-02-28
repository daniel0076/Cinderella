from __future__ import annotations
import logging
from typing import Union
from pathlib import Path
from beancount.core.flags import (
    FLAG_OKAY,
    FLAG_CONVERSIONS,
    FLAG_MERGING,
    FLAG_TRANSFER,
)

from beancount.loader import load_file
from beancount.parser import printer
from beancount.core.data import (
    Transaction,
    Posting,
    filter_txns,
)
from beancount.core.amount import Amount

from cinderella.utils import iterate_files
from cinderella.ledger.datatypes import (
    Ledger,
    Amount as InternalAmount,
    Posting as InternalPosting,
    Transaction as InternalTransaction,
    StatementType,
    TransactionFlag,
)
from cinderella.settings import LOG_NAME

logger = logging.getLogger(LOG_NAME)


def write_accounts_to_beanfile(accounts: list, output_path: str):
    accounts = sorted(list(set(accounts)))

    path = Path(output_path)
    path.parent.mkdir(exist_ok=True, parents=True)
    with open(output_path, "w") as f:
        for account in accounts:
            line = f"2020-01-01 open {account}\n"
            f.write(line)


def transform_flag(flag: TransactionFlag) -> str:
    FLAG_MAPPING = {
        TransactionFlag.OK: FLAG_OKAY,
        TransactionFlag.CONVERSIONS: FLAG_CONVERSIONS,
        TransactionFlag.TRANSFER: FLAG_TRANSFER,
        TransactionFlag.MERGED: FLAG_MERGING,
    }
    return FLAG_MAPPING.get(flag, FLAG_OKAY)


def transform_amount(amount: InternalAmount) -> Amount:
    return Amount(amount.quantity, amount.currency)


def transform_postings(posting: InternalPosting) -> Posting:
    price = transform_amount(posting.price) if posting.price else None
    return Posting(
        posting.account,
        transform_amount(posting.amount),
        None,  # cost
        price,
        None,  # flag
        None,  # meta
    )


def transform_meta(meta: dict) -> dict:
    commented_meta = {}
    for key, value in meta.items():
        commented_meta[f";{key}"] = value
    return commented_meta


def transform_transaction(
    txn: InternalTransaction, postings: list[Posting]
) -> Transaction:
    payee = None
    tags = set()
    links = set()
    return Transaction(
        transform_meta(txn.meta),
        txn.datetime_.date(),
        transform_flag(txn.flag),
        payee,
        txn.title,
        tags,
        links,
        postings,
    )


def transform_ledger(ledger: Ledger) -> list[Transaction]:
    entries = []
    for txn in ledger.transactions:
        b_postings = []
        for posting in txn.postings:
            b_postings.append(transform_postings(posting))
        entries.append(transform_transaction(txn, b_postings))

    return entries


def load_beanfile_to_internal_transactions(
    path: Union[Path, str]
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

    return convert_to_internal_transactions(transactions)


def convert_to_internal_transactions(
    transactions: list[Transaction],
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


def print_beans(ledger: Ledger, filepath: str = "", mode: str = "a"):
    if filepath:
        entries = transform_ledger(ledger)
        with open(filepath, mode) as f:
            printer.print_entries(entries, file=f)
    else:
        printer.print_entries(ledger.transactions)


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
