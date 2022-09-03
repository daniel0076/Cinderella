import pandas as pd
from dataclasses import dataclass
from datetime import datetime
from abc import abstractmethod
from pathlib import Path

from settings import SourceSettings, StatementSettings
from datatypes import StatementCategory


@dataclass
class ProcessedResult:
    success: bool = False
    type: StatementCategory = StatementCategory.invalid
    data: pd.DataFrame = pd.DataFrame()
    date: datetime.date = datetime.now().date()


class ProcessorBase:
    def __init__(self, settings: SourceSettings):
        settings_by_type = {}
        for statement_settings in settings.statements:
            settings_by_type[statement_settings.type] = statement_settings
        self.settings_by_type = settings_by_type

        functions_by_type = {
            StatementCategory.creditcard: self.process_creditcard,
            StatementCategory.bank: self.process_bank,
            StatementCategory.receipt: self.process_receipt,
        }
        self.functions_by_type = functions_by_type

    def get_settings(self, type: StatementCategory) -> StatementSettings:
        return self.settings_by_type[type]

    def process(self, filepath: Path) -> ProcessedResult:
        filepath_str = filepath.as_posix()

        for statement_type in self.settings_by_type.keys():
            if statement_type.value in filepath_str:
                statement_settings = self.settings_by_type.get(statement_type)
                if not statement_settings:
                    return ProcessedResult(False)

                process_function = self.functions_by_type.get(statement_type)
                if not process_function:
                    return ProcessedResult(False)
                return process_function(filepath_str, statement_settings)

    @abstractmethod
    def process_creditcard(cls, filepath: str) -> ProcessedResult:
        raise NotImplementedError

    @abstractmethod
    def process_bank(cls, filepath: str) -> ProcessedResult:
        raise NotImplementedError

    @abstractmethod
    def process_receipt(cls, filepath: str) -> ProcessedResult:
        raise NotImplementedError
