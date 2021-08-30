from datatypes import Directives
from abc import ABC, abstractmethod
import pandas as pd
import logging

LOGGER = logging.getLogger("StatementLoader")
logging.basicConfig(level=logging.INFO)


class StatementParser(ABC):
    identifier = ""

    def __init__(self):
        self.parser = {
            "bank": self._parse_bank_statement,
            "card": self._parse_card_statement,
            "stock": self._parse_stock_statement,
            "receipt": self._parse_receipt
        }
        self.default_source_accounts = {}

    def parse(self, category: str, df: pd.DataFrame) -> Directives:
        return self.parser[category](df)

    def read_statement(self, filepath: str) -> pd.DataFrame:
        if filepath.endswith("xls") or filepath.endswith("xlsx"):
            return pd.read_excel(filepath)
        elif filepath.endswith("csv"):
            return pd.read_csv(filepath)

    @abstractmethod
    def _parse_card_statement(self, df: pd.DataFrame) -> Directives:
        raise NotImplemented

    @abstractmethod
    def _parse_bank_statement(self, df: pd.DataFrame) -> Directives:
        raise NotImplemented

    @abstractmethod
    def _parse_stock_statement(self, df: pd.DataFrame) -> Directives:
        raise NotImplemented

    def _parse_receipt(self, df: pd.DataFrame) -> Directives:
        raise NotImplemented

    def _parse_price(self, raw_str: str) -> tuple:
        raise NotImplemented
