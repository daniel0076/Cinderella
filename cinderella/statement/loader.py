from __future__ import annotations  # required for TYPE_CHECKING
import logging
from typing import Dict, Iterator, Union, Iterable
from copy import deepcopy
from collections import defaultdict
from pathlib import Path
from typing import TYPE_CHECKING

from anyio.streams import file
from fontTools.feaLib.ast import Statement

from cinderella.statement.datatypes import ExecutionResult
from cinderella.statement.parsers import registry
from cinderella.settings import LOG_NAME, StatementSettings
from cinderella.utils import iterate_files
from cinderella.ledger.datatypes import StatementType

if TYPE_CHECKING:
    from cinderella.ledger.datatypes import Ledger
    from .parsers.base import StatementParser


logger = logging.getLogger(LOG_NAME)


class StatementLoader:
    def __init__(self, statement_settings: StatementSettings):
        self.parsers: Dict[str, StatementParser] = registry.get_parsers()
        self.statement_settings = statement_settings

    def get_all_statement_accounts(self) -> list:
        accounts = []
        for parser in self.parsers.values():
            accounts += parser.get_statement_accounts().values()
        return accounts

    def _find_parser(self, path: str) -> Union[StatementParser, None]:
        for parser in self.parsers.values():
            if parser.source_name in path:
                return parser
        return None

    def _load_file_to_ledgers(self, path: Path) -> Iterator[Ledger]:
        logger.debug("Loading statement files")
        for file in iterate_files(path):
            logger.debug(f"Current file: {file.as_posix()}")
            parser = self._find_parser(file.as_posix())

            if not parser:
                logger.debug(f"No parser found for file: {file.as_posix()}")
                continue

            logger.debug(f"File: {file.as_posix()}, Parser: {parser.source_name}")
            ledger = parser.parse(file)
            if ledger.typ == StatementType.invalid:
                logger.warning(f"Failed to load statement file: {file.as_posix()}")
                continue

            yield ledger

    def _tailor_type_to_ledgers(
        self, ledgers: Iterable[Ledger]
    ) -> dict[StatementType, list[Ledger]]:
        """
        Tailor the statements and return {StatementType: [Ledger]},
        each ledger holds the transactions of a source
        """
        # collect all ledger one by one files
        source_type_to_ledger: dict[frozenset, Ledger] = dict()
        for ledger in ledgers:
            key = frozenset((ledger.source, ledger.typ))
            try:
                source_type_to_ledger[key] += ledger
            except KeyError:
                # don't modify the input for better testibility, and its not costy
                source_type_to_ledger[key] = deepcopy(ledger)

        # tailor the dict from {(source_name, type): Ledger} to {type: [Ledger]}
        typed_ledgers: dict[StatementType, list[Ledger]] = defaultdict(list)
        for ledger in source_type_to_ledger.values():
            typed_ledgers[ledger.typ].append(ledger)

        return typed_ledgers

    def load(self, path: Union[Path, str]) -> dict[StatementType, list[Ledger]]:
        """
        Load the statements and return {StatementType: [Ledger]},
        """
        if isinstance(path, str):
            path = Path(path)

        ledgers = self._load_file_to_ledgers(path)
        return self._tailor_type_to_ledgers(ledgers)

    def preprocess_statements(self) -> ExecutionResult:
        # delegate each source folder to each parser
        for parser in self.parsers.values():
            input_dir = (
                Path(self.statement_settings.input_statement_folder)
                / parser.source_name
            )
            if not input_dir.exists() or not input_dir.is_dir():
                continue

            output_dir = Path(self.statement_settings.preprocessed_statement_folder)
            output_dir.mkdir(parents=True, exist_ok=True)

            result = parser.preprocess(
                input_dir,
                output_dir,
                self.statement_settings.preprocess_settings.get(parser.source_name),
            )
            if result.success:
                logger.info(
                    f"Preprocess for {parser.display_name} completed successfully."
                )

        return ExecutionResult(True)
