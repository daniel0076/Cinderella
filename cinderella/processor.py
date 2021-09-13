from typing import Union
from collections import defaultdict
from datetime import timedelta

from beancount.core.amount import Amount

from cinderella.datatypes import Transactions
from cinderella.beanlayer import BeanCountAPI


class TransactionProcessor:
    def __init__(self):
        self.beancount_api = BeanCountAPI()

    def dedup_transactions(
        self,
        lhs: Union[Transactions, list[Transactions]],
        rhs: Union[Transactions, list[Transactions]] = None,
        lookback_days: int = 0,
        match_negative: bool = False,
    ):
        """
        Remove duplicated Transaction in one or two groups of Transaction.

            Parameters:
                lhs: Transactions or list of Transactions to be deduped
                rhs: Optional, another list of Transactions. When provided, dedup against lhs.

            Returns:
                None, modified in-place
        """
        transactions_list = []
        if isinstance(lhs, Transactions):
            transactions_list.append(lhs)
        elif isinstance(lhs, list):
            transactions_list.extend(lhs)

        if isinstance(rhs, Transactions):
            transactions_list.append(rhs)
        elif isinstance(rhs, list):
            transactions_list.extend(rhs)

        lookback_days_perm = range(-lookback_days, lookback_days + 1)

        bucket = set()
        for transactions in transactions_list:
            unique = []
            for t in transactions:
                duplicated = False
                for i in lookback_days_perm:
                    d = timedelta(days=i)
                    if match_negative:
                        key = (t.date + d, str(Amount.__neg__(t.postings[0].units)), t.narration)
                    else:
                        key = (t.date + d, str(t.postings[0].units), t.narration)

                    if key in bucket:
                        duplicated = True
                        break

                if not duplicated:
                    key = (t.date, str(t.postings[0].units), t.narration)
                    unique.append(t)
                    bucket.add(key)

            transactions.clear()
            transactions.extend(unique)

    def merge_similar_transactions(
        self,
        lhs: Union[Transactions, list[Transactions]],
        rhs: Union[Transactions, list[Transactions]],
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
