import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from copy import deepcopy

from cinderella.transaction import TransactionProcessor
from cinderella.datatypes import Transaction, Ledger, StatementType, Posting


@pytest.fixture
def transaction_processor():
    yield TransactionProcessor()


@pytest.fixture
def hash_by_date_title_amount():
    def hash_function(transaction: Transaction, date_delta: int):
        result = (
            transaction.datetime_.date() + timedelta(days=date_delta),
            transaction.postings[0].amount,
            transaction.title,
        )
        return result

    return hash_function


class TestDeduper:
    @pytest.mark.parametrize("tolerance_days, result_len", [(0, 1), (1, 1), (2, 0)])
    def test_lookback(
        self,
        transaction_processor,
        hash_by_date_title_amount,
        sample_transaction_past,
        sample_transaction,
        tolerance_days,
        result_len,
    ):
        ledger1 = Ledger("Source1", StatementType.custom)
        ledger2 = Ledger("Source2", StatementType.custom)
        ledger1.append_txn(sample_transaction_past)
        ledger2.append_txn(sample_transaction)

        transaction_processor.dedup(
            [ledger1, ledger2], hash_by_date_title_amount, tolerance_days
        )
        assert len(ledger1) == 1
        assert len(ledger2) == result_len

    @pytest.mark.parametrize("tolerance_days, result_len", [(0, 1), (1, 1), (2, 0)])
    def test_lookback_reversed_data(
        self,
        transaction_processor,
        hash_by_date_title_amount,
        sample_transaction_past,
        sample_transaction,
        tolerance_days,
        result_len,
    ):
        ledger1 = Ledger("Source1", StatementType.custom)
        ledger2 = Ledger("Source2", StatementType.custom)
        ledger1.append_txn(sample_transaction)
        ledger2.append_txn(sample_transaction_past)

        transaction_processor.dedup(
            [ledger1, ledger2], hash_by_date_title_amount, tolerance_days
        )
        assert len(ledger1) == 1
        assert len(ledger2) == result_len

    @pytest.mark.parametrize("identical_items", [1, 2, 3])
    def test_dedup_at_most_once(
        self,
        transaction_processor,
        hash_by_date_title_amount,
        sample_transaction,
        identical_items,
    ):
        ledger1 = Ledger("Source1", StatementType.custom)
        ledger2 = Ledger("Source2", StatementType.custom)
        ledger1.append_txn(sample_transaction)
        # only one of the two should be deduped
        for _ in range(identical_items):
            ledger2.append_txn(deepcopy(sample_transaction))

        transaction_processor.dedup([ledger1, ledger2], hash_by_date_title_amount)
        assert len(ledger1) == 1
        assert len(ledger2) == identical_items - 1

    def test_merge_posting_on_dups(
        self,
        transaction_processor,
        hash_by_date_title_amount,
        sample_transaction,
    ):
        ledger1 = Ledger("Source1", StatementType.custom)
        ledger2 = Ledger("Source2", StatementType.custom)
        removed_trans: Transaction = deepcopy(sample_transaction)
        appended_trans: Transaction = deepcopy(sample_transaction)
        appended_trans.insert_comment("Source1", "appended_trans")
        removed_trans.insert_comment("Source2", "removed_trans")
        ledger1.append_txn(appended_trans)
        ledger2.append_txn(removed_trans)

        transaction_processor.dedup(
            [ledger1, ledger2],
            hash_by_date_title_amount,
            merge_dup_txns=True,
        )
        assert len(ledger1) == 1
        assert len(ledger2) == 0
        appended_trans = ledger1.transactions[0]
        assert appended_trans.meta == {
            "Source1": "appended_trans",
            "Source2": "removed_trans",
        }


class TestSpecifiedTransactionProcessor:
    def test_dedup_by_title_and_amount(self, transaction_processor, sample_transaction):
        ledger1 = Ledger("Source1", StatementType.custom)
        ledger2 = Ledger("Source2", StatementType.custom)
        ledger1.append_txn(deepcopy(sample_transaction))
        ledger2.append_txn(deepcopy(sample_transaction))

        transaction_processor.dedup_by_title_and_amount([ledger1, ledger2])
        assert len(ledger1) == 1
        assert len(ledger2) == 0

    def test_dedup_by_account_and_postings_on_bank(
        self, beancount_api, transaction_processor
    ):
        ledger1 = Ledger("Source1", StatementType.bank)
        ledger2 = Ledger("Source2", StatementType.bank)
        posting_from = Posting.create_simple("Asset:Bank1:Test", Decimal(-100), "TWD")
        posting_to = Posting.create_simple("Asset:Bank2:Test", Decimal(100), "TWD")

        today = datetime.today()
        t1 = Transaction(today, "bank1", [posting_from, posting_to])
        t2 = Transaction(today, "bank2", [posting_to, posting_from])
        ledger1.append_txn(t1)
        ledger2.append_txn(t2)

        transaction_processor.dedup_bank_transfer([ledger1, ledger2])
        assert len(ledger1) == 1
        assert len(ledger2) == 0


class TestUtilFunction:
    @pytest.mark.parametrize(
        "lookback_days, expected",
        [(0, [0]), (1, [0, 1, -1]), (2, [0, 1, -1, 2, -2]), (-1, [])],
    )
    def test_gen_lookback_perm(self, transaction_processor, lookback_days, expected):
        result = transaction_processor._gen_lookback_perm(lookback_days)
        assert result == expected
