from zoneinfo import ZoneInfo
import pandas as pd
import pytest
from datetime import datetime
from decimal import Decimal
from cinderella.statement.parsers.cryptocom import CryptoCom
from cinderella.ledger.datatypes import Transaction, Ledger, StatementType


@pytest.fixture
def parser():
    yield CryptoCom()


class TestCryptoCom:
    def test_parse_creditcard_statement(self, parser: CryptoCom):
        df = pd.DataFrame(
            {
                "COL0": ["2021-01-31 01:23:45"],
                "COL1": ["Title"],
                "COL2": ["TWD"],
                "COL3": ["-100.0"],
                "COL4": [""],
                "COL5": [""],
                "COL6": ["SGD"],
                "COL7": ["-4"],
                "COL8": ["-3"],
            }
        )
        expected = Ledger(parser.source_name, StatementType.creditcard)
        taiwan_tz = ZoneInfo("Asia/Taipei")
        txn = Transaction(datetime(2021, 1, 31, 1, 23, 45).astimezone(taiwan_tz), "Title (-100.0 TWD)")
        txn.create_and_append_posting(
            parser.statement_accounts[StatementType.creditcard],
            Decimal("-3"),
            "USD",
        )
        expected.append_txn(txn)

        result = parser.parse_creditcard_statement(df)
        assert expected == result
