from typing import Union
from collections import defaultdict
from datetime import timedelta

from cinderella.datatypes import Transactions
from cinderella.beanlayer import BeanCountAPI


class TransactionProcessor:
    def __init__(self):
        self.beancount_api = BeanCountAPI()

    def dedup_bank_transfer(
        self,
        transactions_list: list,
        lookback_days: int = 0,
    ):
        """
        Remove duplicated Transaction in one or two groups of Transaction.
        Transactions with identical account in the given time period are deemed duplicated

            Parameters:
                lhs: Transactions or list of Transactions to be deduped
                rhs: Optional, another list of Transactions. When provided, dedup against lhs.

            Returns:
                None, modified in-place
        """
        lookback_days_perm = range(-lookback_days, lookback_days + 1)

        bucket = defaultdict(list)
        for transactions in transactions_list:
            unique = []
            for t in transactions:
                duplicated = False
                for i in lookback_days_perm:
                    delta = timedelta(days=i)
                    postings_key = frozenset(
                        [(p.account, p.units) for p in t.postings]
                    )
                    key = (t.date + delta, postings_key)

                    if len(bucket[key]) == 0:
                        continue

                    for existing_t in bucket[key]:
                        if t.postings[0] == existing_t.postings[0]:
                            # do not dedup transactions from the same source
                            continue
                        duplicated = True
                        bucket[key].remove(existing_t)
                        break

                if duplicated:
                    continue

                postings_key = frozenset(
                    [(p.account, p.units) for p in t.postings]
                )
                key = (t.date, postings_key)
                unique.append(t)
                bucket[key].append(t)

            transactions.clear()
            transactions.extend(unique)

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
