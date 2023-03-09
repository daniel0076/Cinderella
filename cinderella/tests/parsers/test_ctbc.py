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
        expected.create_and_append_txn(
            datetime(2023, 1, 1, 0, 0, 0),
            "Test(Remarks 123): Notes",
            parser.statement_accounts[StatementType.bank],
            Decimal("1000"),
            "TWD",
        )

        result = parser.parse_bank_statement(df)
        assert expected == result

    def test_parse_creditcard_statement(self, parser: CTBC):
        df = pd.DataFrame(
            {
                "消費日": ["2023/01/01"],
                "COL1": ["VAL1"],
                "摘要": ["Title"],
                "COL3": [""],
                "COL4": [""],
                "COL5": [""],
                "COL6": ["TW"],
                "COL7": ["1234"],
                "新臺幣金額": ["1000"],
            }
        )
        expected = Ledger(parser.source_name, StatementType.creditcard)
        expected.create_and_append_txn(
            datetime(2023, 1, 1, 0, 0, 0),
            "Title",
            parser.statement_accounts[StatementType.creditcard],
            Decimal("-1000"),
            "TWD",
        )

        result = parser.parse_creditcard_statement(df)
        assert expected == result
