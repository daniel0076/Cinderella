from __future__ import annotations  # for typing
from dataclasses import dataclass, field
from typing import List, Optional, Union
from dacite.core import from_dict
from dacite.config import Config
from enum import Enum
from cinderella.datatypes import StatementType


@dataclass
class StatementDetails:
    type: StatementType = StatementType.invalid
    subject_keyword: str = ".*"  # regex supported
    attachment_keyword: str = ".*"  # regex supported
    valid_senders: List[str] = field(default_factory=list)


@dataclass
class SourceSettings:
    name: str
    enabled: bool
    statements: List[StatementDetails]


@dataclass
class MailSettings:
    server: str
    username: str
    password: str
    output_directory: str
    sources: List[SourceSettings] = field(default_factory=list)

    def __post_init__(self):
        if not self.output_directory:
            raise ValueError(
                "output_directory cannot be empty, please check your configuration file"
            )


@dataclass
class DownloaderSettings:
    mail_settings: Optional[MailSettings]

    @staticmethod
    def from_dict(config: dict) -> tuple[bool, Union[str, DownloaderSettings]]:
        try:
            settings = from_dict(
                data_class=DownloaderSettings, data=config, config=Config(cast=[Enum])
            )
        except Exception as e:
            return False, "{}: {}".format(__name__, e)

        return True, settings
