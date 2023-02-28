import pandas as pd
import pytest
from datetime import datetime
from decimal import Decimal
from cinderella.statement.parsers.ctbc import CTBC
from cinderella.ledger.datatypes import Ledger, StatementType


@pytest.fixture
def parser():
    yield CTBC()


class TestCTBC:
    def test_parse_bank_statement(self, parser: CTBC):
        df = pd.DataFrame(
            {
                "日期": ["2023/01/01"],
                "摘要": ["Test"],
                "支出": [""],
                "存入": ["1000"],
                "結餘": ["1000"],
                "備註": ["Remarks"],
                "轉出入帳號": ["123"],
                "註記": ["Notes"],
            }
        )
        expected = Ledger(parser.source_name, StatementType.bank)
        txn = expected.create_and_append_txn(
            datetime(2023, 1, 1, 0, 0, 0),
            "Test",
            parser.statement_accounts[StatementType.bank],
            Decimal("1000"),
            "TWD",
        )
        txn.insert_comment(f"{parser.display_name}-Acc.", "123")
        txn.insert_comment(f"{parser.display_name}-Remarks", "Remarks")
        txn.insert_comment(f"{parser.display_name}-Notes", "Notes")

        result = parser.parse_bank_statement(df)
        assert expected == result
