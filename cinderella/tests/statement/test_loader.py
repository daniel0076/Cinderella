import pytest
from unittest.mock import patch
from datetime import datetime
from cinderella.statement.loader import StatementLoader
from cinderella.ledger.datatypes import Ledger, Transaction
from cinderella.statement.datatypes import StatementType


@pytest.fixture
def statement_loader():
    with patch("cinderella.statement.loader.get_parsers", return_value=[]):
        yield StatementLoader()


class TestStatementLoader:
    def test_tailor_type_to_ledgers(self, statement_loader):
        # Prepare
        bank1_ledger1 = Ledger(
            "bank1", StatementType.bank, [Transaction(datetime.now(), "bank1_ledger1")]
        )
        bank1_ledger2 = Ledger(
            "bank1", StatementType.bank, [Transaction(datetime.now(), "bank1_ledger2")]
        )
        bank2_ledger1 = Ledger(
            "bank2", StatementType.bank, [Transaction(datetime.now(), "bank2_ledger1")]
        )
        bank2_ledger2 = Ledger(
            "bank2", StatementType.bank, [Transaction(datetime.now(), "bank2_ledger2")]
        )

        ledgers = [
            bank1_ledger1,
            bank1_ledger2,
            bank2_ledger1,
            bank2_ledger2,
        ]

        # Test
        result = statement_loader._tailor_type_to_ledgers(ledgers)

        # Assert
        assert dict(result) == {
            StatementType.bank: [
                bank1_ledger1 + bank1_ledger2,
                bank2_ledger1 + bank2_ledger2,
            ]
        }
