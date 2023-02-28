import pandas as pd
import pytest
from datetime import datetime
from decimal import Decimal
from cinderella.statement.parsers.esun import ESun
from cinderella.ledger.datatypes import Ledger, StatementType


@pytest.fixture
def parser():
    yield ESun()


class TestESun:
    def test_parse_bank_statement(self, parser: ESun):
        df = pd.DataFrame(
            {
                "COL1": ["2023-01-01 01:23:45"],
                "COL2": ["Test"],
                "COL3": [""],  # withdraw
                "COL4": ["1000"],  # deposit
                "COL5": ["1000"],  # balance
                "COL6": ["Remarks"],
            }
        )
        expected = Ledger(parser.source_name, StatementType.bank)
        txn = expected.create_and_append_txn(
            datetime(2023, 1, 1, 1, 23, 45),
            "Test",
            parser.statement_accounts[StatementType.bank],
            Decimal("1000"),
            "TWD",
        )
        txn.insert_comment(f"{parser.display_name}", "Remarks")

        result = parser.parse_bank_statement(df)
        assert expected == result
