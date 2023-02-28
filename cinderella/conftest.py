import pytest
from decimal import Decimal
from datetime import datetime, timedelta

from cinderella.external.beancountapi import BeanCountAPI
from cinderella.ledger.datatypes import Transaction, Posting, Amount


@pytest.fixture
def beancount_api():
    yield BeanCountAPI()


@pytest.fixture
def sample_transaction_narration():
    yield "SAMPLE_TRANS"


@pytest.fixture
def another_transaction_narration():
    yield "ANOTHER_TRANS"


@pytest.fixture
def sample_account():
    yield "Income:Sample"


@pytest.fixture
def another_account():
    yield "Income:Another"


@pytest.fixture
def sample_amount():
    yield Amount(Decimal("100.00"), "TWD")


@pytest.fixture
def another_amount():
    yield Amount(Decimal("101.00"), "TWD")


@pytest.fixture
def sample_posting(sample_account, sample_amount):
    yield Posting(sample_account, sample_amount)


@pytest.fixture
def another_posting(another_account, another_amount):
    yield Posting(another_account, another_amount)


@pytest.fixture
def sample_transaction(sample_posting, sample_transaction_narration):
    yield Transaction(
        datetime.now(), sample_transaction_narration, [sample_posting], {}
    )


@pytest.fixture
def another_transaction(another_posting, another_transaction_narration):
    yield Transaction(
        datetime.now(), another_transaction_narration, [another_posting], {}
    )


@pytest.fixture
def sample_transaction_past(sample_posting, sample_transaction_narration):
    yield Transaction(
        datetime.now() + timedelta(days=-2),
        sample_transaction_narration,
        [sample_posting],
        {},
    )
