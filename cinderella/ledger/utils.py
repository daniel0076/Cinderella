from typing import Dict, List, Callable
from collections import defaultdict
from datetime import timedelta
from dataclasses import dataclass

from .datatypes import StatementType, Transaction, Ledger, OnExistence


def gen_lookback_perm(n: int) -> List:
    if n < 0:
        return []

    result = [0]
    for i in range(1, n + 1):
        result.extend([i, -i])
    return result


def dedup(
    ledgers: list[Ledger],
    hash_function: Callable,
    tolerance_days: int = 0,
    ignore_same_source: bool = True,
    merge_dup_txns: bool = False,
    merge_txn_postings: bool = False,
    specify_statement_types: list[StatementType] = [],
    custom_diff_check_hook: Callable[[Transaction, Transaction], bool] = (
        lambda _, __: False
    ),
) -> None:
    """
    Remove duplicated Transaction with the hash function
    """

    @dataclass
    class DedupRecord:
        source: str
        txn: Transaction
        found_dup: bool = False

    # use list as there might be multiple transactions with common date and postings
    dedup_map: Dict[str, List[DedupRecord]] = defaultdict(list)
    tolerance_days_perm = gen_lookback_perm(tolerance_days)

    for ledger in ledgers:
        if specify_statement_types and ledger.typ not in specify_statement_types:
            continue

        unique_transactions = []
        for curr_txn in ledger.transactions:
            tolerance_keys = [
                hash_function(curr_txn, date_delta)
                for date_delta in tolerance_days_perm
            ]
            duplicated = False
            for key in tolerance_keys:
                for dedup_record in dedup_map.get(key, []):
                    if dedup_record.found_dup:
                        continue
                    if ignore_same_source and ledger.source == dedup_record.source:
                        continue
                    if custom_diff_check_hook(dedup_record.txn, curr_txn):
                        continue

                    duplicated = True
                    dedup_record.found_dup = True
                    if merge_dup_txns:
                        dedup_record.txn.merge(
                            curr_txn,
                            comment_exists=OnExistence.RENAME,
                            merge_postings=merge_txn_postings,
                        )
                    break

                if duplicated:  # stop looking back after a dup item is found
                    break
            if duplicated:  # early return on dup item
                continue

            key = hash_function(curr_txn, 0)
            unique_transactions.append(curr_txn)
            dedup_map[key].append(DedupRecord(ledger.source, curr_txn, False))

        ledger.transactions.clear()
        ledger.transactions.extend(unique_transactions)


def dedup_bank_transfer(
    ledgers: list[Ledger],
    tolerance_days: int = 0,
):
    print("Deduping bank transfer and conversions...", end="")

    # same postings, with tolerance
    # different postings, same date
    def hash_function(transaction: Transaction, date_delta: int):
        postings = frozenset(
            [(posting.account, posting.amount) for posting in transaction.postings]
        )
        result = (
            transaction.datetime_.date() + timedelta(days=date_delta),
            postings,
        )
        return result

    def same_first_posting_as_diff(lhs: Transaction, rhs: Transaction) -> bool:
        return lhs.postings[0] == rhs.postings[0]

    dedup(
        ledgers,
        hash_function,
        tolerance_days,
        ignore_same_source=False,
        specify_statement_types=[StatementType.bank],
        custom_diff_check_hook=same_first_posting_as_diff,
    )
    print("done")


def dedup_by_title_and_amount(
    ledgers: list[Ledger],
    tolerance_days: int = 0,
):
    """
    Remove duplicated Transaction the list from left to right
    Items on the LHS has higher priority, duplicated items on the RHS are removed
    Transactions with identical title and amount in the given time period are deemed duplicated

        Returns:
            None, modified in-place
    """

    def hash_function(transaction: Transaction, date_delta: int):
        result = (
            transaction.datetime_.date() + timedelta(days=date_delta),
            transaction.postings[0].amount,
            transaction.title,
        )
        return result

    dedup(ledgers, hash_function, tolerance_days)


def merge_same_date_amount(
    ledgers: list[Ledger],
    tolerance_days: int = 0,
) -> None:
    """
    merge identical transactions from rhs to lhs
    two transactions are deemed identical if they have common date and amount
    """

    def hash_function(transaction: Transaction, lookback_days: int):
        return (
            transaction.datetime_.date() + timedelta(days=lookback_days),
            transaction.postings[0].amount,
        )

    dedup(ledgers, hash_function, tolerance_days, merge_dup_txns=True)
