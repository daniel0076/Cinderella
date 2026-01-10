import logging
import os
import pandas as pd
from abc import ABC
from pathlib import Path
from typing import Optional

from cinderella.ledger.classifier import Union
from cinderella.settings import LOG_NAME, AfterPreprocessAction, PreprocessSettings
from cinderella.ledger.datatypes import StatementType, Ledger
from cinderella.statement.datatypes import (
    ExecutionResult,
    PreprocessResult,
    StatementAttributes,
)
from cinderella.external.beancountapi import make_statement_accounts
from . import registry


class StatementParser(ABC):
    """
    Base class for statement parsers, contains two main parts:
    1. Preprocessing raw statement files, such as unzip, decrypt, decode, etc.
    2. Parsing statement files into Ledger objects
    """

    source_name = ""
    display_name = ""
    supported_statement_types: list[StatementType] = []

    def __init__(self):
        self.logger = logging.getLogger(LOG_NAME)
        self.statement_accounts: dict[StatementType, str] = make_statement_accounts(
            self.supported_statement_types, self.display_name
        )

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

        # Allow abstract subclasses
        if cls is StatementParser:
            return

        if cls.source_name == "":
            raise TypeError(f"{cls.__name__} must define class attribute 'source_name'")

        if cls.display_name == "":
            raise TypeError(
                f"{cls.__name__} must define class attribute 'display_name'"
            )

        if not cls.supported_statement_types:
            raise TypeError(
                f"{cls.__name__} must define class attribute 'supported_statement_types'"
            )

        # ---- auto-register ----
        registry.register(cls.source_name, cls)

    def get_supported_statement_types(self) -> list[StatementType]:
        return self.supported_statement_types

    def parse(self, path: Path) -> Ledger:
        df = self._read_csv(path)
        if StatementType.checking.value in path.as_posix():
            return self.parse_checking_statement(df)
        elif StatementType.creditcard.value in path.as_posix():
            return self.parse_creditcard_statement(df)
        elif StatementType.receipt.value in path.as_posix():
            return self.parse_receipt_statement(df)
        else:
            self.logger.warning(
                f"No StatementType found for {path.as_posix()}, skipping"
            )
            return Ledger("Invalid", StatementType.invalid)

    def _read_csv(self, path: Path) -> pd.DataFrame:
        df = pd.read_csv(path.as_posix())
        return df

    def get_statement_accounts(self) -> dict:
        return self.statement_accounts

    def parse_creditcard_statement(
        self, records: pd.DataFrame, attrs: Optional[StatementAttributes] = None
    ) -> Ledger:
        self.logger.warning(f"CreditCard is not supported by {self.display_name}")
        return Ledger(self.source_name, StatementType.invalid)

    def parse_checking_statement(
        self, records: pd.DataFrame, attrs: Optional[StatementAttributes] = None
    ) -> Ledger:
        self.logger.warning(f"Bank is not supported by {self.display_name}")
        return Ledger(self.source_name, StatementType.invalid)

    def parse_receipt_statement(
        self, records: pd.DataFrame, attrs: Optional[StatementAttributes] = None
    ) -> Ledger:
        self.logger.warning(f"Receipt is not supported by {self.display_name}")
        return Ledger(self.source_name, StatementType.invalid)

    """
    Preprocess raw statement files into ready-to-parse files.
    """

    def preprocess(
        self,
        input_statement_dir: Path,
        output_statement_dir: Path,
        all_preprocess_settings: Optional[dict[StatementType, PreprocessSettings]],
    ) -> Union[ExecutionResult[PreprocessResult], ExecutionResult[str]]:
        for supported_type in self.supported_statement_types:
            preprocess_settings = None
            if all_preprocess_settings:
                preprocess_settings = all_preprocess_settings.get(supported_type)

            if supported_type == StatementType.checking:
                func = self.preprocess_checking_statement
            elif supported_type == StatementType.creditcard:
                func = self.preprocess_creditcard_statement
            elif supported_type == StatementType.receipt:
                func = self.preprocess_receipt_statement
            else:
                self.logger.warning(
                    f"Preprocess for {supported_type.name} is not supported by {self.display_name}"
                )
                continue

            for input_statement in input_statement_dir.iterdir():
                if not input_statement.is_file():
                    continue
                result = func(
                    input_statement,
                    output_statement_dir / supported_type.value,
                    preprocess_settings,
                )
                if result.success:
                    self.logger.info(
                        f"Preprocessing {supported_type.value} statements for {self.source_name} succeeded."
                    )
                    processed_files = result.message
                    assert isinstance(processed_files, list)
                    self.after_preprocess(
                        input_statement_dir, processed_files, preprocess_settings
                    )
                else:
                    self.logger.error(
                        f"Preprocessing {supported_type.value} statements for {self.source_name} failed: {result.message}"
                    )

        return ExecutionResult(True)

    def preprocess_creditcard_statement(
        self,
        input_statement: Path,
        output_dir: Path,
        preprocess_settings: Optional[PreprocessSettings],
    ) -> ExecutionResult[PreprocessResult]:
        return ExecutionResult(True)

    def preprocess_checking_statement(
        self,
        input_statement: Path,
        output_dir: Path,
        preprocess_settings: Optional[PreprocessSettings],
    ) -> ExecutionResult[PreprocessResult]:
        return ExecutionResult(True)

    def preprocess_receipt_statement(
        self,
        input_statement: Path,
        output_dir: Path,
        preprocess_settings: Optional[PreprocessSettings],
    ) -> ExecutionResult[PreprocessResult]:
        return ExecutionResult(True)

    def after_preprocess(
        self,
        source_dir: Path,
        files: list[Path],
        settings: Optional[PreprocessSettings],
    ):
        """
        post process operations, like moving the files
        """
        for file in files:
            if not file.exists():
                return
            after_preprocessed_action = None
            if settings is not None:
                after_preprocessed_action = settings.after_processed
            else:
                return

            if after_preprocessed_action == AfterPreprocessAction.move:
                dst_directory = Path(source_dir) / settings.archive_folder
                os.makedirs(dst_directory, exist_ok=True)

                dst = dst_directory / file.name
                os.rename(file, dst)
            elif after_preprocessed_action == AfterPreprocessAction.delete:
                os.remove(file)
            else:
                raise ValueError(
                    f"Unknown after_preprocessed_action: {after_preprocessed_action}"
                )
