import pandas as pd
from abc import ABC, abstractmethod

from cinderella.external.beancount.utils import BeanCountAPI
from cinderella.statement.datatypes import Transactions, StatementType


class StatementParser(ABC):
    identifier = ""

    def __init__(self):
        self.default_source_accounts = {}
        self.beancount_api = BeanCountAPI()

    def parse(self, category: StatementType, filepath: str) -> Transactions:
        df = self._read_statement(filepath)
        if category == StatementType.bank:
            return self._parse_bank_statement(df)
        elif category == StatementType.creditcard:
            return self._parse_card_statement(df)
        elif category == StatementType.stock:
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
