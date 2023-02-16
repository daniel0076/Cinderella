from typing import Union, Callable
from collections import defaultdict
from datetime import timedelta

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
        """
        Remove duplicated Transaction in N > 1 groups of Transaction.
        Transactions with identical account in the given time period are deemed duplicated

            Parameters:
                lhs: Transactions or list of Transactions to be deduped
                rhs: Optional, another list of Transactions. When provided, dedup against lhs.

            Returns:
                None, modified in-place
        """

        if len(transactions_list) < 2:
            return

        # use list as there might be multiple transactions with common date and postings
        unique_transactions_bucket = defaultdict(list)
        # a transaction have at most one duplicated item,
        # use a list of bool to record if a dup item has been found
        transaction_deduped_record = defaultdict(list)

        lookback_days_perm = range(-lookback_days, 1)

        for transactions in transactions_list:
            if transactions.category != StatementType.bank:
                continue

            unique_transactions = []
            for current_transaction in transactions:
                postings = frozenset([(posting.account, posting.units)
                                     for posting in current_transaction.postings])
                transaction_lookback_keys = [(current_transaction.date + timedelta(delta), postings)
                                             for delta in lookback_days_perm]
                duplicated = False
                for key in transaction_lookback_keys:
                    for index, existing_transaction in enumerate(unique_transactions_bucket.get(key, [])):
                        if current_transaction.postings[0] == existing_transaction.postings[0]:
                            continue  # do not dedup transactions from the same source
                        if transaction_deduped_record[key][index]:
                            continue
                        duplicated = True
                        transaction_deduped_record[key][index] = True
                        break

                    if duplicated:  # stop looking back after a dup item is found
                        break
                if duplicated:  # early return on dup item
                    continue

                key = (current_transaction.date, postings)
                unique_transactions.append(current_transaction)
                unique_transactions_bucket[key].append(current_transaction)
                transaction_deduped_record[key].append(False)

            transactions.clear()
            transactions.extend(unique_transactions)

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
        if isinstance(lhs, Transactions):
            lhs = [lhs]
        if isinstance(rhs, Transactions):
            rhs = [rhs]

        lookback_days_perm = range(-lookback_days, lookback_days + 1)

        bucket = defaultdict(int)
        for transactions in lhs:
            for t in transactions:
                key = (t.date, t.postings[0].units, t.narration)
                bucket[key] += 1

        for transactions in rhs:
            unique = []
            for t in transactions:
                duplicated = False
                for i in lookback_days_perm:
                    d = timedelta(days=i)
                    key = (t.date + d, t.postings[0].units, t.narration)

                    if bucket[key]:
                        bucket[key] -= 1
                        duplicated = True
                        break

                if not duplicated:
                    unique.append(t)

            transactions.clear()
            transactions.extend(unique)

    def merge_same_date_amount(
        self,
        lhs: Union[Transactions, list[Transactions]],
        rhs: Union[Transactions, list[Transactions]],
        lookback_days: int = 0,
    ) -> None:
        """
        merge similar transactions from rhs to lhs
        two transactions are deemed similar if they have common date and amount
        """
        if isinstance(lhs, Transactions):
            lhs = [lhs]
        if isinstance(rhs, Transactions):
            rhs = [rhs]

        # build map for comparison
        bucket: dict[tuple, list] = defaultdict(list)
        for transactions in lhs:
            for t in transactions:
                key = (t.date, t.postings[0].units)
                bucket[key].append(t)

        lookback_days_perm = range(-lookback_days, lookback_days + 1)
        for transactions in rhs:
            unique = []
            for t in transactions:
                duplicated = False
                for i in lookback_days_perm:
                    d = timedelta(days=i)
                    key = (t.date + d, t.postings[0].units)
                    if len(bucket[key]) > 0:
                        existing_t = bucket[key][-1]
                        self.beancount_api.merge_transactions(
                            existing_t, t, keep_dest_accounts=False
                        )
                        bucket[key].pop()
                        duplicated = True
                        break

                if not duplicated:
                    unique.append(t)
            transactions.clear()
            transactions.extend(unique)
