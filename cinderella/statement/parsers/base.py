from html import parser
import logging
import os
from black import output
import pandas as pd
from abc import ABC
from pathlib import Path
from typing import Optional

from cinderella.ledger.classifier import Union
from cinderella.settings import LOG_NAME, PreprocessSettings, StatementSettings
from cinderella.ledger.datatypes import StatementType, Ledger
from cinderella.statement.datatypes import (
    ExecutionResult,
    StatementAttributes,
)
from cinderella.external.beancountapi import make_statement_accounts
from . import registry
from cinderella.statement.utils import move_to_folder


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
        input_dir: Path,
        output_dir: Path,
        statement_settings: StatementSettings,
    ) -> ExecutionResult[str]:
        parser_preprocess_settings = statement_settings.preprocess_settings.get(
            self.source_name
        )
        for statement_type in self.supported_statement_types:
            input_statement_dir = input_dir / statement_type.value
            if not input_statement_dir.exists():
                continue
            output_statement_dir = output_dir / statement_type.value

            if statement_type == StatementType.checking:
                func = self.preprocess_checking_statement
            elif statement_type == StatementType.creditcard:
                func = self.preprocess_creditcard_statement
            elif statement_type == StatementType.receipt:
                func = self.preprocess_receipt_statement
            else:
                self.logger.warning(
                    f"Preprocess for {statement_type.name} is not supported by {self.display_name}"
                )
                continue

            for input_statement in input_statement_dir.iterdir():
                if not input_statement.is_file():
                    continue

                # Get preprocess settings for this statement type
                if parser_preprocess_settings is not None:
                    typed_setting = parser_preprocess_settings.get(statement_type)
                else:
                    typed_setting = None

                result = func(
                    input_statement,
                    output_statement_dir,
                    typed_setting,
                )
                if result.success:
                    self.logger.info(
                        f"Preprocessing {statement_type.value} statements for {self.source_name} succeeded."
                    )
                    move_to_folder(
                        input_statement_dir,
                        Path(statement_settings.archive_statement_folder)
                        / self.source_name
                        / statement_type.value,
                    )
                else:
                    self.logger.error(
                        f"Preprocessing {statement_type.value} statements for {self.source_name} failed: {result.message}"
                    )

        return ExecutionResult(True)

    def preprocess_creditcard_statement(
        self,
        input_statement: Path,
        output_dir: Path,
        preprocess_settings: Optional[PreprocessSettings],
    ) -> ExecutionResult:
        """
        Default behavior: move the file to output_dir without any changes.
        """
        move_to_folder(input_statement, output_dir)
        return ExecutionResult(True)

    def preprocess_checking_statement(
        self,
        input_statement: Path,
        output_dir: Path,
        preprocess_settings: Optional[PreprocessSettings],
    ) -> ExecutionResult:
        """
        Default behavior: move the file to output_dir without any changes.
        """
        move_to_folder(input_statement, output_dir)
        return ExecutionResult(True)

    def preprocess_receipt_statement(
        self,
        input_statement: Path,
        output_dir: Path,
        preprocess_settings: Optional[PreprocessSettings],
    ) -> ExecutionResult:
        """
        Default behavior: move the file to output_dir without any changes.
        """
        move_to_folder(input_statement, output_dir)
        return ExecutionResult(True)
