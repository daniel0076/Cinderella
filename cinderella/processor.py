from typing import Union
from collections import defaultdict

from cinderella.datatypes import Transactions
from cinderella.beanlayer import BeanCountAPI


class TransactionProcessor:
    def __init__(self):
        self.beancount_api = BeanCountAPI()

    def dedup_transactions(
        self,
        lhs: Union[Transactions, list[Transactions]],
        rhs: Union[Transactions, list[Transactions]] = None,
    ):
        """
        Remove duplicated Transaction in one or two groups of Transaction.

            Parameters:
                lhs: Transactions or list of Transactions to be deduped
                rhs: Optional, another list of Transactions

            Returns:
                None, modified in-place
        """
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
