import os
from dataclasses import dataclass
from abc import abstractmethod, ABC
from pathlib import Path
import logging

from cinderella.settings import StatementSettings, RawStatementProcessSettings
from cinderella.datatypes import StatementType, AfterProcessedAction
from cinderella.settings import LOG_NAME


@dataclass
class ProcessedResult:
    success: bool = False
    message: str = ""


class ProcessorBase(ABC):
    source_name = "ProcessorBase"

    def __init__(self, settings: StatementSettings):
        self.output_dir = settings.ready_statement_folder
        self.move_dir = settings.backup_statement_folder
        self.settings = settings

        settings_by_type: dict[StatementType, RawStatementProcessSettings] = {}
        for setting in settings.raw_statement_processing.get(self.source_name, []):
            settings_by_type[setting.statement_type] = setting
        self.settings_by_type = settings_by_type

        self.process_functions = {
            StatementType.creditcard: self.process_creditcard,
            StatementType.bank: self.process_bank,
            StatementType.receipt: self.process_receipt,
        }

    def process(self, file: Path) -> ProcessedResult:
        """
        Process the file using a source processor based on the type hint from the file name
        """
        logger = logging.getLogger(LOG_NAME)

        file_str = file.as_posix()
        for statement_type in self.process_functions.keys():
            if statement_type.value not in file_str:
                continue

            process_settings = self.settings_by_type.get(statement_type, None)
            if not process_settings:
                relative_filename = file.relative_to(
                    self.settings.raw_statement_folder
                ).as_posix()
                logger.info(
                    f"Using default preprocessing settings for {relative_filename}"
                )
                process_settings = RawStatementProcessSettings(
                    statement_type, "", AfterProcessedAction.move
                )

            result: ProcessedResult = self.process_functions[statement_type](
                file, process_settings
            )
            if result.success:
                # execute action after processed
                self.post_process(file, process_settings)

            return result

        return ProcessedResult(False, f"No process function for {file}")

    def post_process(self, file: Path, settings: RawStatementProcessSettings):
        """
        post process operations, like moving the files
        """
        if not file.exists():
            return

        after_processed = settings.after_processed
        if after_processed == AfterProcessedAction.move:
            dst_directory = Path(
                self.move_dir, settings.statement_type.value, type(self).source_name
            )
            os.makedirs(dst_directory, exist_ok=True)

            dst = dst_directory / file.name
            os.rename(file, dst)
        elif after_processed == AfterProcessedAction.delete:
            os.remove(file)
        elif after_processed == AfterProcessedAction.keep:
            pass

    @abstractmethod
    def process_creditcard(
        cls, file: Path, settings: RawStatementProcessSettings
    ) -> ProcessedResult:
        pass

    @abstractmethod
    def process_bank(
        cls, file: Path, settings: RawStatementProcessSettings
    ) -> ProcessedResult:
        pass

    @abstractmethod
    def process_receipt(
        cls, file: Path, settings: RawStatementProcessSettings
    ) -> ProcessedResult:
        pass
