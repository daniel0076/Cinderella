import pandas as pd
import pytest
from datetime import datetime
from decimal import Decimal
from cinderella.statement.parsers.invos import Invos
from cinderella.ledger.datatypes import Ledger, StatementType


@pytest.fixture
def parser():
    yield Invos()


class TestInvos:
    def test_parse_receipt_statement(self, parser: Invos):
        df = pd.DataFrame(
            {
                "消費日期": ["1100101", "1100101"],
                "消費品項": ["Item1", "Item2"],
                "單價": ["50", "50"],
                "個數": ["1.0", "1.0"],
                "小計": ["50", "50"],
                "店家名稱": ["Vendor1", "Vendor1"],
            }
        )
        expected = Ledger(parser.source_name, StatementType.receipt)
        txn = expected.create_and_append_txn(
            datetime(2021, 1, 1, 0, 0, 0),
            "Vendor1",
            parser.statement_accounts[StatementType.receipt],
            Decimal("-100"),
            "TWD",
        )
        txn.meta = {
            f"{parser.display_name}(0)": "Item1 - 1.0*50",
            f"{parser.display_name}(1)": "Item2 - 1.0*50",
        }

        result = parser.parse_receipt_statement(df)
        assert expected == result
