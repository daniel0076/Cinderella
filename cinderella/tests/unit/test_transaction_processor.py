import pytest
from copy import deepcopy

from cinderella.processor import TransactionProcessor
from cinderella.datatypes import Transactions


@pytest.fixture
def transaction_processor():
    yield TransactionProcessor()


class TestTransactionProcessor:
    def test_dedup_different_source(
        self, transaction_processor, sample_transaction, another_transaction
    ):
        trans1 = Transactions()
        trans2 = Transactions()
        trans1.append(deepcopy(sample_transaction))
        trans2.append(deepcopy(sample_transaction))
        trans2.append(deepcopy(another_transaction))
        trans2.append(deepcopy(another_transaction))

        transaction_processor.dedup_transactions(trans1, trans2)
        assert len(trans1) == 1
        assert len(trans2) == 1

    def test_dedup_same_source(self, transaction_processor, sample_transaction):
        trans1 = Transactions()
        trans1.append(deepcopy(sample_transaction))
        trans1.append(deepcopy(sample_transaction))
        trans1.append(deepcopy(sample_transaction))

        transaction_processor.dedup_transactions(trans1)
        assert len(trans1) == 1

    def test_dedup_using_list(self, transaction_processor, sample_transaction):
        trans1 = Transactions()
        trans2 = Transactions()
        trans1.append(deepcopy(sample_transaction))
        trans2.append(deepcopy(sample_transaction))

        transaction_processor.dedup_transactions([trans1], [trans2])
        assert len(trans1) == 1
        assert len(trans2) == 0

    def test_dedup_lookback_days(
        self, transaction_processor, sample_transaction, sample_transaction_past
    ):
        trans1 = Transactions()
        trans2 = Transactions()
        trans1.append(sample_transaction)
        trans2.append(sample_transaction_past)

        transaction_processor.dedup_transactions(trans1, trans2)
        assert len(trans1) == 1
        assert len(trans2) == 1

        transaction_processor.dedup_transactions(trans1, trans2, lookback_days=1)
        assert len(trans1) == 1
        assert len(trans2) == 1

        transaction_processor.dedup_transactions(trans1, trans2, lookback_days=2)
        assert len(trans1) == 1
        assert len(trans2) == 0
