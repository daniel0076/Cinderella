import pandas as pd
import pytest
from datetime import datetime
from decimal import Decimal
from cinderella.statement.parsers.post import TaiwanPost
from cinderella.ledger.datatypes import Transaction, Ledger, StatementType


@pytest.fixture
def parser():
    yield TaiwanPost()


class TestTaiwanPost:
    def test_parse_bank_statement(self, parser: TaiwanPost):
        df = pd.DataFrame(
            {
                "COL0": ["110/01/01 02:34:56", "110/01/01 02:34:56"],  # datetime
                "COL1": ["Test", "Test"],  # title
                "COL2": ["", ""],
                "COL3": ["100", "0"],  # withdraw
                "COL4": ["", ""],  # deposit
                "COL5": ["100", "100"],  # balance
                "COL6": ["RemarksShould", "BeConcated"],  # info
                "COL7": ["", "Notes"],  # remarks
            }
        )
        expected = Ledger(parser.source_name, StatementType.bank)
        txn = Transaction(datetime(2021, 1, 1, 2, 34, 56), "Test")
        txn.create_and_append_posting(
            parser.statement_accounts[StatementType.bank],
            Decimal("-100"),
            "TWD",
        )
        txn.insert_comment(f"{parser.display_name}-Remarks", "RemarksShouldBeConcated")
        txn.insert_comment(f"{parser.display_name}-Notes", "Notes")
        expected.append_txn(txn)

        result = parser.parse_bank_statement(df)
        assert expected == result
