import pandas as pd
from abc import ABC, abstractmethod

from beanlayer import BeanCountAPI

from datatypes import Transactions


class StatementParser(ABC):
    identifier = ""

    def __init__(self):
        self.default_source_accounts = {}
        self.beancount_api = BeanCountAPI()

    def parse(self, category: str, filepath: str) -> Transactions:
        df = self._read_statement(filepath)
        if category == "bank":
            return self._parse_bank_statement(df)
        elif category == "card":
            return self._parse_card_statement(df)
        else:
            raise NotImplementedError

    def _read_statement(self, filepath: str) -> pd.DataFrame:
        if filepath.endswith("xls") or filepath.endswith("xlsx"):
            return pd.read_excel(filepath)
        elif filepath.endswith("csv"):
            return pd.read_csv(filepath)

    @abstractmethod
    def _parse_card_statement(self, df: pd.DataFrame) -> Transactions:
        raise NotImplementedError

    @abstractmethod
    def _parse_bank_statement(self, df: pd.DataFrame) -> Transactions:
        raise NotImplementedError
