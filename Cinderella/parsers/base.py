from datatypes import Directives
from abc import ABC, abstractmethod
import pandas as pd
import logging

LOGGER = logging.getLogger("StatementLoader")


class StatementParser(ABC):
    identifier = ""

    def __init__(self):
        self.default_source_accounts = {}

    def parse(self, category: str, filepath: str) -> Directives:
        df = self._read_statement(filepath)
        if category == "bank":
            return self._parse_bank_statement(df)
        elif category == "card":
            return self._parse_card_statement(df)
        else:
            raise NotImplemented

    def _read_statement(self, filepath: str) -> pd.DataFrame:
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
