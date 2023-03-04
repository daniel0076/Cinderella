import pandas as pd
import pytest
from datetime import datetime
from decimal import Decimal
from cinderella.statement.parsers.sinopac import Sinopac
from cinderella.ledger.datatypes import Ledger, StatementType


@pytest.fixture
def parser():
    yield Sinopac()


class TestSinopac:
    def test_parse_bank_statement(self, parser: Sinopac):
        df = pd.DataFrame(
            {
                "交易日": ["2023/01/01 12:34"],
                "計息日": [""],
                "摘要": ["Test"],
                "支出": [""],
                "存入": ["1000"],
                "餘額": ["1000"],
                "匯率": [""],
                "備註/資金用途": ["Notes"],
            }
        )
        expected = Ledger(parser.source_name, StatementType.bank)
        txn = expected.create_and_append_txn(
            datetime(2023, 1, 1, 12, 34, 0),
            "Test",
            parser.statement_accounts[StatementType.bank],
            Decimal("1000"),
            "TWD",
        )
        txn.insert_comment(f"{parser.display_name}", "Notes")

        result = parser.parse_bank_statement(df)
        assert expected == result

    def test_parse_creditcard_statement(self, parser: Sinopac):
        df = pd.DataFrame(
            {
                "COL0": ["2023/01/01"],
                "COL1": ["2023/01/01"],
                "COL2": ["123"],
                "COL3": ["Title"],
                "COL4": ["100"],
            }
        )
        expected = Ledger(parser.source_name, StatementType.creditcard)
        expected.create_and_append_txn(
            datetime(2023, 1, 1),
            "Title",
            parser.statement_accounts[StatementType.creditcard],
            Decimal("-100"),
            "TWD",
        )

        result = parser.parse_creditcard_statement(df)
        assert expected == result
