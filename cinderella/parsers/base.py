import pandas as pd
from abc import ABC, abstractmethod

from cinderella.beanlayer import BeanCountAPI
from cinderella.datatypes import Transactions, StatementCategory


class StatementParser(ABC):
    identifier = ""

    def __init__(self):
        self.default_source_accounts = {}
        self.beancount_api = BeanCountAPI()

    def parse(self, category: StatementCategory, filepath: str) -> Transactions:
        df = self._read_statement(filepath)
        if category == StatementCategory.bank:
            return self._parse_bank_statement(df)
        elif category == StatementCategory.card:
            return self._parse_card_statement(df)
        elif category == StatementCategory.stock:
            return self._parse_stock_statement(df)
        else:
            raise NotImplementedError

    def _read_statement(self, filepath: str) -> pd.DataFrame:
        return pd.read_csv(filepath)

    @abstractmethod
    def _parse_card_statement(self, df: pd.DataFrame) -> Transactions:
        pass

    @abstractmethod
    def _parse_bank_statement(self, df: pd.DataFrame) -> Transactions:
        pass

    def _parse_stock_statement(self, df: pd.DataFrame) -> Transactions:
        pass
