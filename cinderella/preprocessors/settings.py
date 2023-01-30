from __future__ import annotations  # for typing
from dataclasses import dataclass, field
from typing import List
from dacite.core import from_dict
from dacite.config import Config
from enum import Enum

from datatypes import StatementType, AfterProcessedAction


@dataclass
class StatementSettings:
    type: StatementType = StatementType.invalid
    password: str = ""
    after_processed: AfterProcessedAction = AfterProcessedAction.keep


@dataclass
class SourceSettings:
    name: str
    statements: List[StatementSettings] = field(default_factory=list)


@dataclass
class ProcessorSettings:
    input_directory: str
    output_directory: str
    move_directory: str
    sources: List[SourceSettings] = field(default_factory=list)

    @staticmethod
    def from_dict(config: dict) -> tuple[bool, ProcessorSettings | str]:
        try:
            settings = from_dict(
                data_class=ProcessorSettings, data=config, config=Config(cast=[Enum])
            )
        except Exception as e:
            return False, "{}: {}".format(__name__, e)

        return True, settings
