import pandas as pd
import pytest
from datetime import datetime
from decimal import Decimal
from cinderella.statement.datatypes import StatementAttributes
from cinderella.statement.parsers.cathay import Cathay, CathayUSD
from cinderella.ledger.datatypes import Transaction, Ledger, StatementType


@pytest.fixture
def cathay_parser():
    yield Cathay()


@pytest.fixture
def cathayusd_parser():
    yield CathayUSD()


class TestCathay:
    def test_parse_creditcard_statement(self, cathay_parser: Cathay):
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
        expected = Ledger(cathay_parser.source_name, StatementType.creditcard)
        txn = Transaction(datetime(2021, 1, 31, 0, 0), "Test")
        txn.create_and_append_posting(
            cathay_parser.statement_accounts[StatementType.creditcard],
            Decimal("-100"),
            "TWD",
        )
        expected.append_txn(txn)

        result = cathay_parser.parse_creditcard_statement(
            df, StatementAttributes(year=2021, month=1)
        )
        assert expected == result

    def test_parse_bank_statement(self, cathay_parser: Cathay):
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
        expected = Ledger(cathay_parser.source_name, StatementType.bank)
        txn = Transaction(
            datetime(2023, 1, 1, 15, 10, 1), "Operation(AccountNo): Remarks"
        )
        txn.create_and_append_posting(
            cathay_parser.statement_accounts[StatementType.bank],
            Decimal("100"),
            "TWD",
        )
        expected.append_txn(txn)

        result = cathay_parser.parse_bank_statement(df)
        assert expected == result


class TestCathayUSD:
    def test_parse_bank_statement(self, cathayusd_parser: CathayUSD):
        df = pd.DataFrame(
            {
                "COL0": ["2023/01/01"],  # date
                "COL1": ["15:10:01"],  # time
                "COL2": ["存入"],  # withdraw
                "COL3": ["100"],  # deposit
                "COL4": ["100"],  # balance
                "COL5": ["Remarks"],  # remarks
                "COL6": ["Operation"],
            }
        )
        expected = Ledger(cathayusd_parser.source_name, StatementType.bank)
        txn = Transaction(datetime(2023, 1, 1, 15, 10, 1), "Operation: Remarks")
        txn.create_and_append_posting(
            cathayusd_parser.statement_accounts[StatementType.bank],
            Decimal("100"),
            "USD",
        )
        expected.append_txn(txn)

        result = cathayusd_parser.parse_bank_statement(df)
        assert expected == result
