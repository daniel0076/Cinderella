from __future__ import annotations  # for typing
from dataclasses import dataclass, field
from typing import List, Union
from dacite.core import from_dict
from dacite.config import Config
from enum import Enum

from datatypes import StatementCategory, AfterProcessedAction


@dataclass
class StatementSettings:
    type: StatementCategory = StatementCategory.invalid
    password: str = ""
    after_processed: AfterProcessedAction = AfterProcessedAction.keep

@dataclass
class SourceSettings:
    identifier: str
    statements: List[StatementSettings] = field(default_factory=list)

@dataclass
class PDFProcessorSettings:
    input_directory: str
    output_directory: str
    move_directory: str
    sources: List[SourceSettings] = field(default_factory=list)

    @staticmethod
    def from_dict(config: dict) -> tuple[bool, Union[PDFProcessorSettings]]:
        try:
            settings = from_dict(data_class=PDFProcessorSettings,
                                 data=config, config=Config(cast=[Enum]))
        except Exception as e:
            return False, "{}: {}".format(__name__, e)

        return True, settings
