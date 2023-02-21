import logging
import pandas as pd
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING
from pathlib import Path

from cinderella.settings import LOG_NAME
from cinderella.statement.datatypes import StatementType

if TYPE_CHECKING:
    from cinderella.ledger.datatypes import Ledger


class StatementParser(ABC):
    identifier = ""

    def __init__(self):
        self.default_source_accounts = {}
        self.logger = logging.getLogger(LOG_NAME)

    def parse(self, path: Path) -> Ledger:
        df = self._read_statement(path)
        if StatementType.bank.value in path.as_posix():
            return self._parse_bank_statement(df)
        elif StatementType.creditcard.value in path.as_posix():
            return self._parse_card_statement(df)
        elif StatementType.receipt.value in path.as_posix():
            return self._parse_receipt_statement(df)
        else:
            self.logger.warning(
                f"No StatementType found for {path.as_posix()}, skipping"
            )
            return Ledger("Invalid", StatementType.invalid)

    def _read_statement(self, path: Path) -> pd.DataFrame:
        return pd.read_csv(path.as_posix())

    @abstractmethod
    def _parse_card_statement(self, df: pd.DataFrame) -> Ledger:
        pass

    @abstractmethod
    def _parse_bank_statement(self, df: pd.DataFrame) -> Ledger:
        pass

    @abstractmethod
    def _parse_receipt_statement(self, df: pd.DataFrame) -> Ledger:
        pass
