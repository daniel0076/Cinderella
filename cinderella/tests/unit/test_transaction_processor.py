import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from copy import deepcopy

from beancount.core.data import Transaction
from cinderella.transaction import TransactionProcessor
from cinderella.datatypes import Transactions, StatementType


@pytest.fixture
def transaction_processor():
    yield TransactionProcessor()


@pytest.fixture
def hash_by_date_title_amount():
    def hash_function(transaction: Transaction, date_delta: int):
        result = (
            transaction.date + timedelta(days=date_delta),
            transaction.postings[0].units,
            transaction.narration,
        )
        return result

    return hash_function


class TestDeduper:
    @pytest.mark.parametrize("lookback_days, result_len", [(0, 1), (1, 1), (2, 0)])
    def test_lookback(
        self,
        transaction_processor,
        hash_by_date_title_amount,
        sample_transaction_past,
        sample_transaction,
        lookback_days,
        result_len,
    ):
        trans_list_1 = Transactions(StatementType.custom, "Transactions1")
        trans_list_2 = Transactions(StatementType.custom, "Transactions2")
        trans_list_1.append(sample_transaction_past)
        trans_list_2.append(sample_transaction)

        transaction_processor.dedup(
            [trans_list_1, trans_list_2],
            hash_by_date_title_amount,
            lookback_days=lookback_days,
        )
        assert len(trans_list_1) == 1
        assert len(trans_list_2) == result_len

    @pytest.mark.parametrize("lookback_days, result_len", [(0, 1), (1, 1), (2, 0)])
    def test_lookback_reversed_data(
        self,
        transaction_processor,
        hash_by_date_title_amount,
        sample_transaction_past,
        sample_transaction,
        lookback_days,
        result_len,
    ):
        trans_list_1 = Transactions(StatementType.custom, "Transactions1")
        trans_list_2 = Transactions(StatementType.custom, "Transactions2")
        trans_list_1.append(sample_transaction)
        trans_list_2.append(sample_transaction_past)

        transaction_processor.dedup(
            [trans_list_1, trans_list_2],
            hash_by_date_title_amount,
            lookback_days=lookback_days,
        )
        assert len(trans_list_1) == 1
        assert len(trans_list_2) == result_len

    @pytest.mark.parametrize("identical_items", [1, 2, 3])
    def test_dedup_at_most_once(
        self,
        transaction_processor,
        hash_by_date_title_amount,
        sample_transaction,
        identical_items,
    ):
        trans_list_1 = Transactions(StatementType.custom, "Transactions1")
        trans_list_2 = Transactions(StatementType.custom, "Transactions2")
        trans_list_1.append(sample_transaction)
        # only one of the two should be deduped
        for _ in range(identical_items):
            trans_list_2.append(deepcopy(sample_transaction))

        transaction_processor.dedup(
            [trans_list_1, trans_list_2], hash_by_date_title_amount
        )
        assert len(trans_list_1) == 1
        assert len(trans_list_2) == identical_items - 1

    def test_merge_posting_on_dups(
        self,
        beancount_api,
        transaction_processor,
        hash_by_date_title_amount,
        sample_transaction,
    ):
        trans_list_1 = Transactions(StatementType.custom, "Transactions1")
        trans_list_2 = Transactions(StatementType.custom, "Transactions2")
        removed_trans = deepcopy(sample_transaction)
        appended_trans = deepcopy(sample_transaction)
        beancount_api.add_transaction_comment(removed_trans, "removed_trans")
        beancount_api.add_transaction_comment(appended_trans, "appended_trans")
        beancount_api.add_posting_comment(removed_trans, "removed_posting", index=0)
        beancount_api.add_posting_comment(appended_trans, "appended_posting", index=0)
        trans_list_1.append(removed_trans)
        trans_list_2.append(appended_trans)

        transaction_processor.dedup(
            [trans_list_1, trans_list_2],
            hash_by_date_title_amount,
            merge_duplicates=True,
        )
        assert len(trans_list_1) == 1
        assert len(trans_list_2) == 0
        appended_trans = trans_list_1[0]
        assert appended_trans.meta == {
            ";1": "removed_trans",
            ";2": "appended_trans",
        }
        assert appended_trans.postings[0].meta == {
            ";1": "removed_posting",
            ";2": "appended_posting",
        }


class TestSpecifiedTransactionProcessor:
    def test_dedup_by_title_and_amount(self, transaction_processor, sample_transaction):
        trans1 = Transactions(StatementType.custom, "Transactions1")
        trans2 = Transactions(StatementType.custom, "Transactions2")
        trans1.append(deepcopy(sample_transaction))
        trans2.append(deepcopy(sample_transaction))

        transaction_processor.dedup_by_title_and_amount([trans1, trans2])
        assert len(trans1) == 1
        assert len(trans2) == 0

    def test_dedup_by_account_and_postings_on_bank(
        self, beancount_api, transaction_processor
    ):
        # Arrange
        trans1 = Transactions(category=StatementType.bank, source="bank1")
        trans2 = Transactions(category=StatementType.bank, source="bank2")
        postings_from = beancount_api.make_simple_posting(
            "Asset:Bank1:Test", Decimal(-100), "TWD"
        )
        postings_to = beancount_api.make_simple_posting(
            "Asset:Bank2:Test", Decimal(100), "TWD"
        )

        today = datetime.today()
        t1 = beancount_api.make_transaction(
            today, "bank1", [postings_from, postings_to]
        )
        t2 = beancount_api.make_transaction(
            today, "bank2", [postings_to, postings_from]
        )
        trans1.append(t1)
        trans2.append(t2)

        transaction_processor.dedup_bank_transfer([trans1, trans2])
        assert len(trans1) == 1
        assert len(trans2) == 0


class TestUtilFunction:
    @pytest.mark.parametrize(
        "lookback_days, expected",
        [(0, [0]), (1, [0, 1, -1]), (2, [0, 1, -1, 2, -2]), (-1, [])],
    )
    def test_gen_lookback_perm(self, transaction_processor, lookback_days, expected):
        result = transaction_processor._gen_lookback_perm(lookback_days)
        assert result == expected
