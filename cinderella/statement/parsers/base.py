import logging
import pandas as pd
from abc import ABC, abstractmethod
from pathlib import Path

from cinderella.settings import LOG_NAME
from cinderella.ledger.datatypes import StatementType
from cinderella.external.beancountapi import make_statement_accounts
from cinderella.ledger.datatypes import Ledger


class StatementParser(ABC):
    source_name = ""
    display_name = ""

    def __init__(self, supported_types: list[StatementType] = []):
        assert supported_types != []
        self.logger = logging.getLogger(LOG_NAME)
        self.statement_accounts: dict[StatementType, str] = make_statement_accounts(
            supported_types, self.display_name
        )
        assert self.source_name != ""
        assert self.display_name != ""

    def parse(self, path: Path) -> Ledger:
        df = self._read_csv(path)
        if StatementType.bank.value in path.as_posix():
            return self.parse_bank_statement(df)
        elif StatementType.creditcard.value in path.as_posix():
            return self.parse_creditcard_statement(df)
        elif StatementType.receipt.value in path.as_posix():
            return self.parse_receipt_statement(df)
        else:
            self.logger.warning(
                f"No StatementType found for {path.as_posix()}, skipping"
            )
            return Ledger("Invalid", StatementType.invalid)

    def _read_csv(self, path: Path) -> pd.DataFrame:
        df = pd.read_csv(path.as_posix())
        return df

    def get_statement_accounts(self) -> dict:
        return self.statement_accounts

    @abstractmethod
    def parse_creditcard_statement(self, df: pd.DataFrame) -> Ledger:
        pass

    @abstractmethod
    def parse_bank_statement(self, df: pd.DataFrame) -> Ledger:
        pass

    @abstractmethod
    def parse_receipt_statement(self, df: pd.DataFrame) -> Ledger:
        pass
