import pandas as pd
import pytest
from datetime import datetime
from decimal import Decimal
from cinderella.statement.parsers.richart import Richart
from cinderella.ledger.datatypes import Transaction, Ledger, StatementType


@pytest.fixture
def richart_parser():
    yield Richart()


class TestRichart:
    def test_parse_creditcard_statement(self, richart_parser: Richart):
        df = pd.DataFrame(
            {
                "消費日期": ["2021-01-31"],
                "COL1": ["VAL1"],
                "COL2": ["VAL2"],
                "金額": ["-NT$100"],
                "消費明細": ["TEST"],
                "COL5": ["VAL5"],
                "COL6": ["VAL6"],
                "COL7": ["VAL7"],
            }
        )
        expected = Ledger(richart_parser.source_name, StatementType.creditcard)
        txn = Transaction(datetime(2021, 1, 31, 0, 0), "TEST")
        txn.create_and_append_posting(
            richart_parser.statement_accounts[StatementType.creditcard],
            Decimal("-100"),
            "TWD",
        )
        expected.append_txn(txn)

        result = richart_parser.parse_creditcard_statement(df)
        assert expected == result
