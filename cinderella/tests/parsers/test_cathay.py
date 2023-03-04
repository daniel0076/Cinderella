import pandas as pd
import pytest
from datetime import datetime
from decimal import Decimal
from cinderella.statement.parsers.cathay import Cathay
from cinderella.ledger.datatypes import Transaction, Ledger, StatementType


@pytest.fixture
def parser():
    yield Cathay()


class TestCathay:
    def test_parse_creditcard_statement(self, parser: Cathay):
        df = pd.DataFrame(
            {
                "消費日": ["01/31"],
                "COL1": ["VAL1"],
                "交易說明": ["Test"],
                "臺幣金額": ["100"],
                "消費明細": ["TEST"],
                "卡號末四碼": ["1234"],
                "COL6": ["VAL6"],
                "COL7": ["VAL7"],
                "COL8": ["VAL8"],
                "幣別": ["TWD"],
                "外幣金額": [""],
            }
        )
        expected = Ledger(parser.source_name, StatementType.creditcard)
        txn = Transaction(datetime(2021, 1, 31, 0, 0), "Test")
        txn.create_and_append_posting(
            parser.statement_accounts[StatementType.creditcard],
            Decimal("-100"),
            "TWD",
        )
        expected.append_txn(txn)

        result = parser._parse_creditcard_statement(df, 2021, 1)
        assert expected == result

    def test_parse_bank_statement(self, parser: Cathay):
        df = pd.DataFrame(
            {
                "COL0": ["20230101"],  # date
                "COL1": ["151001"],  # time
                "COL2": [""],  # withdraw
                "COL3": ["100"],  # deposit
                "COL4": ["100"],  # balance
                "COL5": ["Operation"],
                "COL6": ["AccountNo"],
                "COL7": ["Remarks"],  # remarks
            }
        )
        expected = Ledger(parser.source_name, StatementType.bank)
        txn = Transaction(
            datetime(2023, 1, 1, 15, 10, 1), "Operation(AccountNo): Remarks"
        )
        txn.create_and_append_posting(
            parser.statement_accounts[StatementType.bank],
            Decimal("100"),
            "TWD",
        )
        expected.append_txn(txn)

        result = parser.parse_bank_statement(df)
        assert expected == result
