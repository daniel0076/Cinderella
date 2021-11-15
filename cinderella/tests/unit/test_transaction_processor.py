import pytest
from decimal import Decimal
from datetime import datetime
from copy import deepcopy

from cinderella.processor import TransactionProcessor
from cinderella.datatypes import Transactions, StatementCategory


@pytest.fixture
def transaction_processor():
    yield TransactionProcessor()


class TestDedupByTitleAndAmount:
    def test_dedup(
        self, transaction_processor, sample_transaction, another_transaction
    ):
        trans1 = Transactions()
        trans2 = Transactions()
        trans1.append(deepcopy(sample_transaction))
        trans2.append(deepcopy(sample_transaction))  # only this one should be deduped
        trans2.append(deepcopy(another_transaction))
        trans2.append(deepcopy(another_transaction))

        transaction_processor.dedup_by_title_and_amount(trans1, trans2)
        assert len(trans1) == 1
        assert len(trans2) == 2

    def test_dedup_using_list(self, transaction_processor, sample_transaction):
        trans1 = Transactions()
        trans2 = Transactions()
        trans1.append(deepcopy(sample_transaction))
        trans2.append(deepcopy(sample_transaction))

        transaction_processor.dedup_by_title_and_amount([trans1], [trans2])
        assert len(trans1) == 1
        assert len(trans2) == 0

    def test_dedup_lookback_days(
        self, transaction_processor, sample_transaction, sample_transaction_past
    ):
        trans1 = Transactions()
        trans2 = Transactions()
        trans1.append(sample_transaction)
        trans2.append(sample_transaction_past)

        transaction_processor.dedup_by_title_and_amount(trans1, trans2)
        assert len(trans1) == 1
        assert len(trans2) == 1

        transaction_processor.dedup_by_title_and_amount(trans1, trans2, lookback_days=1)
        assert len(trans1) == 1
        assert len(trans2) == 1

        transaction_processor.dedup_by_title_and_amount(trans1, trans2, lookback_days=2)
        assert len(trans1) == 1
        assert len(trans2) == 0


class TestDedupBankTransfer:
    def test_dedup(self, beancount_api, transaction_processor):
        # Arrange
        trans1 = Transactions(category=StatementCategory.bank, source="bank1")
        trans2 = Transactions(category=StatementCategory.bank, source="bank2")
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

    def test_dedup_same_source(self, beancount_api, transaction_processor):
        # Arrange
        trans1 = Transactions(category=StatementCategory.bank, source="bank1")
        trans2 = Transactions(category=StatementCategory.bank, source="bank2")
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
        trans2.append(deepcopy(t2))  # only this should be deduped
        trans2.append(deepcopy(t2))

        transaction_processor.dedup_bank_transfer([trans1, trans2])
        assert len(trans1) == 1
        assert len(trans2) == 1
