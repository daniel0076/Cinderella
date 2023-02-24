import logging
import pandas as pd
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING
from pathlib import Path

from cinderella.settings import LOG_NAME
from cinderella.ledger.datatypes import StatementType

if TYPE_CHECKING:
    from cinderella.ledger.datatypes import Ledger


class StatementParser(ABC):
    source_name = ""
    display_name = ""

    def __init__(self):
        self.logger = logging.getLogger(LOG_NAME)
        self.supported_types = [StatementType.invalid]

    def parse(self, path: Path) -> Ledger:
        df = self._read_csv(path)
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

    def _read_csv(self, path: Path) -> pd.DataFrame:
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
