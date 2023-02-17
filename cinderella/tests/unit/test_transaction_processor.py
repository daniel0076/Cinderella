import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from copy import deepcopy

from cinderella.transaction import TransactionProcessor
from cinderella.datatypes import Transactions, StatementType


@pytest.fixture
def transaction_processor():
    yield TransactionProcessor()


class TestDedupByTitleAndAmount:
    def test_dedup(
        self, transaction_processor, sample_transaction, another_transaction
    ):
        trans1 = Transactions(StatementType.custom, "Transactions1")
        trans2 = Transactions(StatementType.custom, "Transactions2")
        trans1.append(deepcopy(sample_transaction))
        trans2.append(deepcopy(sample_transaction))  # only this one should be deduped
        trans2.append(deepcopy(another_transaction))
        trans2.append(deepcopy(another_transaction))

        transaction_processor.dedup_by_title_and_amount(trans1, trans2)
        assert len(trans1) == 1
        assert len(trans2) == 2

    @pytest.mark.parametrize("lookback_days, result_len", [(0, 1), (1, 1), (2, 0)])
    def test_lookback(
        self,
        transaction_processor,
        sample_transaction,
        sample_transaction_past,
        lookback_days,
        result_len,
    ):
        trans1 = Transactions(StatementType.custom, "Transactions1")
        trans2 = Transactions(StatementType.custom, "Transactions2")
        trans1.append(sample_transaction_past)
        trans2.append(sample_transaction)

        transaction_processor.dedup_by_title_and_amount(
            trans1, trans2, lookback_days=lookback_days
        )
        assert len(trans1) == 1
        assert len(trans2) == result_len

    @pytest.mark.parametrize("lookback_days, result_len", [(0, 1), (1, 1), (2, 0)])
    def test_lookback_reversed_data(
        self,
        transaction_processor,
        sample_transaction,
        sample_transaction_past,
        lookback_days,
        result_len,
    ):
        trans1 = Transactions(StatementType.custom, "Transactions1")
        trans2 = Transactions(StatementType.custom, "Transactions2")
        trans1.append(sample_transaction)
        trans2.append(sample_transaction_past)

        transaction_processor.dedup_by_title_and_amount(
            trans1, trans2, lookback_days=lookback_days
        )
        assert len(trans1) == 1
        assert len(trans2) == result_len


class TestDedupBankTransfer:
    @pytest.mark.parametrize("lookback_days, result_len", [(0, 1), (1, 0), (2, 0)])
    def test_lookback(
        self, beancount_api, transaction_processor, lookback_days, result_len
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
        tomorrow = datetime.today() + timedelta(days=1)
        t1 = beancount_api.make_transaction(
            today, "bank1", [postings_from, postings_to]
        )
        t2 = beancount_api.make_transaction(
            tomorrow, "bank2", [postings_to, postings_from]
        )
        trans1.append(t1)
        trans2.append(t2)

        transaction_processor.dedup_bank_transfer(
            [trans1, trans2], lookback_days=lookback_days
        )
        assert len(trans1) == 1
        assert len(trans2) == result_len

    @pytest.mark.parametrize("identical_items", [1, 2, 3])
    def test_dedup_at_most_once(
        self, beancount_api, transaction_processor, identical_items
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
        for _ in range(identical_items):
            trans2.append(deepcopy(t2))  # only one of them should be deduped

        transaction_processor.dedup_bank_transfer([trans1, trans2])
        assert len(trans1) == 1
        assert len(trans2) == identical_items - 1


class TestUtilFunction:
    @pytest.mark.parametrize(
        "lookback_days, expected",
        [(0, [0]), (1, [0, 1, -1]), (2, [0, 1, -1, 2, -2]), (-1, [])],
    )
    def test_gen_lookback_perm(self, transaction_processor, lookback_days, expected):
        result = transaction_processor._gen_lookback_perm(lookback_days)
        assert result == expected
