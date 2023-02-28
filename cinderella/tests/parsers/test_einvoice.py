import pandas as pd
import pytest
from datetime import datetime
from decimal import Decimal
from cinderella.statement.parsers.einvoice import Einvoice
from cinderella.ledger.datatypes import Ledger, StatementType


@pytest.fixture
def parser():
    yield Einvoice()


class TestEinvoice:
    def test_parse_receipt_statement(self, parser: Einvoice):
        df = pd.DataFrame(
            {
                "COL0": ["M", "D"],
                "COL1": ["Random1", "Random2"],
                "COL2": ["Random1", "100"],
                "COL3": ["20230101", "ItemName"],
                "COL4": ["Random1", ""],
                "COL5": ["Title", ""],
                "COL6": ["Random1", ""],
                "COL7": ["100", ""],
                "COL8": ["Random1", ""],
            }
        )
        expected = Ledger(parser.source_name, StatementType.receipt)
        txn = expected.create_and_append_txn(
            datetime(2023, 1, 1, 0, 0, 0),
            "Title",
            parser.statement_accounts[StatementType.receipt],
            Decimal("-100"),
            "TWD",
        )
        txn.insert_comment(f"{parser.display_name}", "ItemName - 100")

        result = parser.parse_receipt_statement(df)
        assert expected == result
