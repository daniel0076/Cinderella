import pytest
from decimal import Decimal
from datetime import datetime, timedelta

from beancount.core.amount import Amount
from beancount.core.data import Transaction, Posting


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
    yield Posting(sample_account, sample_amount, None, None, None, {})


@pytest.fixture
def another_posting(another_account, another_amount):
    yield Posting(another_account, another_amount, None, None, None, {})


@pytest.fixture
def sample_transaction(sample_posting, sample_transaction_narration):
    date = datetime.now().date()
    meta = {}
    yield Transaction(  # type: ignore
        meta,
        date,
        None,
        None,
        sample_transaction_narration,
        set(),
        set(),
        [sample_posting],
    )


@pytest.fixture
def another_transaction(another_posting, another_transaction_narration):
    date = datetime.now().date()
    meta = {}
    yield Transaction(  # type: ignore
        meta,
        date,
        None,
        None,
        another_transaction_narration,
        set(),
        set(),
        [another_posting],
    )


@pytest.fixture
def sample_transaction_past(sample_posting, sample_transaction_narration):
    date = datetime.now().date()
    meta = {}
    yield Transaction(  # type: ignore
        meta,
        date + timedelta(days=-2),
        None,
        None,
        sample_transaction_narration,
        set(),
        set(),
        [sample_posting],
    )
