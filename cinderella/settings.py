from __future__ import annotations
from dataclasses import dataclass, field
from cinderella.statement.datatypes import AfterProcessedAction, StatementType
from typing import Dict
from dacite.core import from_dict
from dacite.config import Config
from enum import Enum
from pprint import pformat
import json


LOG_NAME = "Cinderella"


@dataclass
class SettingsBase:
    @classmethod
    def from_file(cls, path: str):
        with open(path) as fp:
            content = json.load(fp)
        return cls.from_dict(content)

    @classmethod
    def from_dict(cls, config: dict):
        try:
            settings = from_dict(
                data_class=cls, data=config, config=Config(cast=[Enum])
            )
        except Exception as e:
            return False, "{}: {}".format(__name__, e)

        return True, settings

    def __str__(self) -> str:
        return pformat(self, indent=2, compact=True, sort_dicts=True)


@dataclass
class RawStatementProcessSettings(SettingsBase):
    statement_type: StatementType
    password: str
    after_processed: AfterProcessedAction


@dataclass
class StatementSettings(SettingsBase):
    raw_statement_folder: str
    ready_statement_folder: str
    backup_statement_folder: str
    raw_statement_processing: dict[str, list[RawStatementProcessSettings]] = field(
        default_factory=dict
    )


@dataclass
class BeancountSettings(SettingsBase):
    output_beanfiles_folder: str
    ignored_beanfiles_folder: str
    overwrite_beanfiles_folder: str


@dataclass
class LedgerProcessingSettings(SettingsBase):
    transfer_matching_days: int = 1


@dataclass
class CinderellaSettings(SettingsBase):
    statement_settings: StatementSettings
    beancount_settings: BeancountSettings
    ledger_processing_settings: LedgerProcessingSettings
    default_accounts: Dict
    mappings: Dict[str, Dict[str, list[str]]]

    def get_mapping(self, source_name: str):
        return self.mappings.get(source_name, {})
