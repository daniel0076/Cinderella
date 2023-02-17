from typing import Dict, List, Union, Callable
from collections import defaultdict
from datetime import timedelta
from dataclasses import dataclass

from beancount.core.data import Transaction

from cinderella.datatypes import Transactions, StatementType
from cinderella.beanlayer import BeanCountAPI


class TransactionProcessor:
    def __init__(self):
        self.beancount_api = BeanCountAPI()

    def dedup_bank_transfer(
        self,
        transactions_list: list[Transactions],
        lookback_days: int = 0,
    ):
        def hash_function(transaction: Transaction, date_delta: int):
            postings = frozenset(
                [(posting.account, posting.units) for posting in transaction.postings]
            )
            result = (transaction.date + timedelta(days=date_delta), postings)
            return result

        self.dedup(transactions_list, hash_function, lookback_days, StatementType.bank)

    def dedup_by_title_and_amount(
        self,
        lhs: Union[Transactions, list[Transactions]],
        rhs: Union[Transactions, list[Transactions]],
        lookback_days: int = 0,
    ):
        """
        Remove duplicated Transaction in  rhs against lhs.
        Transactions with identical title and amount in the given time period are deemed duplicated

            Returns:
                None, modified in-place
        """

        def hash_function(transaction: Transaction, date_delta: int):
            result = (
                transaction.date + timedelta(days=date_delta),
                transaction.postings[0].units,
                transaction.narration,
            )
            return result

        self.dedup([lhs, rhs], hash_function, lookback_days)

    def merge_same_date_amount(
        self,
        lhs: Union[Transactions, list[Transactions]],
        rhs: Union[Transactions, list[Transactions]],
        lookback_days: int = 0,
    ) -> None:
        """
        merge identical transactions from rhs to lhs
        two transactions are deemed identical if they have common date and amount
        """

        def hash_function(transaction: Transaction, lookback_days: int):
            return (
                transaction.date + timedelta(days=lookback_days),
                transaction.postings[0].units,
            )

        self.dedup([lhs, rhs], hash_function, lookback_days, merge_duplicates=True)

    def dedup(
        self,
        transactions_list: list[Transactions],
        hash_function: Callable,
        lookback_days: int = 0,
        ignore_same_source: bool = True,
        merge_duplicates: bool = False,
        specify_statement_type: StatementType = StatementType.invalid,
    ):
        """
        Remove duplicated Transaction in N > 1 groups of Transaction with the hash function
            Parameters:
                transactions_list: list of Transactions to be deduped
            Returns:
                None, modified in-place
        """
        if len(transactions_list) < 2:
            return

        @dataclass
        class DedupRecord:
            source: str
            transaction: Transaction
            found_dup: bool = False

        # use list as there might be multiple transactions with common date and postings
        dedup_map: Dict[str, List[DedupRecord]] = defaultdict(list)
        lookback_days_perm = self._gen_lookback_perm(lookback_days)

        for transactions in transactions_list:
            if specify_statement_type != StatementType.invalid:
                if transactions.category != specify_statement_type:
                    continue

            unique_transactions = []
            for current_transaction in transactions:
                transaction_lookback_keys = [
                    hash_function(current_transaction, date_delta)
                    for date_delta in lookback_days_perm
                ]
                duplicated = False
                for key in transaction_lookback_keys:
                    for dedup_record in dedup_map.get(key, []):
                        if dedup_record.found_dup:
                            continue
                        if (
                            ignore_same_source
                            and transactions.source == dedup_record.source
                        ):
                            continue
                        duplicated = True
                        dedup_record.found_dup = True
                        if merge_duplicates:
                            self.beancount_api.merge_transactions(
                                dedup_record.transaction,
                                current_transaction,
                                keep_dest_accounts=False,
                            )
                        break

                    if duplicated:  # stop looking back after a dup item is found
                        break
                if duplicated:  # early return on dup item
                    continue

                key = hash_function(current_transaction, 0)
                unique_transactions.append(current_transaction)
                dedup_map[key].append(
                    DedupRecord(transactions.source, current_transaction, False)
                )

            transactions.clear()
            transactions.extend(unique_transactions)

    def _gen_lookback_perm(self, n: int) -> List:
        if n < 0:
            return []

        result = [0]
        for i in range(1, n + 1):
            result.extend([i, -i])
        return result
