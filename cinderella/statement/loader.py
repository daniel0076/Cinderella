from __future__ import annotations  # required for TYPE_CHECKING
import logging
from typing import Iterator, Union, Iterable
from copy import deepcopy
from collections import defaultdict
from pathlib import Path
from typing import TYPE_CHECKING
from .parsers import get_parsers
from cinderella.settings import LOG_NAME
from cinderella.utils import iterate_files

if TYPE_CHECKING:
    from cinderella.ledger.datatypes import Ledger, StatementType
    from .parsers.base import StatementParser


logger = logging.getLogger(LOG_NAME)


class StatementLoader:
    def __init__(self):
        self.parsers: list[StatementParser] = []
        for parser_cls in get_parsers():
            self.parsers.append(parser_cls())

    def get_all_statement_accounts(self) -> list:
        accounts = []
        for parser in self.parsers:
            accounts += parser.get_statement_accounts().values()
        return accounts

    def _find_parser(self, path: str) -> Union[StatementParser, None]:
        for parser in self.parsers:
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
