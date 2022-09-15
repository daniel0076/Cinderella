import os
from dataclasses import dataclass
from abc import abstractmethod, ABC
from pathlib import Path

from settings import SourceSettings, StatementSettings
from datatypes import StatementCategory, AfterProcessedAction


@dataclass
class ProcessedResult:
    success: bool = False
    message: str = ""


class ProcessorBase(ABC):
    source_name = "ProcessorBase"

    def __init__(
        self, output_dir_format: str, move_dir_format: str, settings: SourceSettings
    ):
        self.output_dir_format = output_dir_format
        self.move_dir_format = move_dir_format
        self.settings = settings

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

    def process(self, file: Path) -> ProcessedResult:
        """
        Process the file using a source processor based on the type hint from the file name
        """

        file_str = file.as_posix()
        statement_type = "Unknown"
        for statement_type in self.settings_by_type.keys():
            if statement_type.value not in file_str:
                continue

            statement_settings = self.settings_by_type.get(statement_type)
            if not statement_settings:
                return ProcessedResult(
                    False, f"Statement settings for {statement_type} not found"
                )

            process_function = self.functions_by_type.get(statement_type)
            if not process_function:
                return ProcessedResult(
                    False, f"Process function for {statement_type} not found"
                )

            result: ProcessedResult = process_function(file_str)
            if result.success:
                # execute action after processed
                self.post_process(file, statement_type)

            return result

        return ProcessedResult(False, f"Unsupported {statement_type} for {file}")

    def post_process(self, file: Path, statement_type: StatementCategory):
        """
        post process operations, like moving the files
        """

        after_processed = self.settings_by_type[statement_type].after_processed
        if after_processed == AfterProcessedAction.move:
            dst_directory = Path(
                self.move_dir_format.format(
                    source_name=type(self).source_name,
                    statement_type=statement_type.value,
                )
            )
            os.makedirs(dst_directory, exist_ok=True)

            dst = dst_directory / file.name
            os.rename(file, dst)
        elif after_processed == AfterProcessedAction.delete:
            os.remove(file)
        elif after_processed == AfterProcessedAction.keep:
            pass

    @abstractmethod
    def process_creditcard(cls, file: str) -> ProcessedResult:
        pass

    @abstractmethod
    def process_bank(cls, file: str) -> ProcessedResult:
        pass

    @abstractmethod
    def process_receipt(cls, file: str) -> ProcessedResult:
        pass
