from __future__ import annotations  # for typing
from dataclasses import dataclass
from typing import Dict
from dacite.core import from_dict
from dacite.config import Config
from enum import Enum
import json


@dataclass
class MainSettings:
    statements_directory: str
    output_directory: str
    ignored_bean_keyword: str
    custom_bean_keyword: str
    default_accounts: Dict
    mappings: Dict

    def get_mapping(self, source_name: str):
        return self.mappings.get(source_name, {})

    @staticmethod
    def from_file(path: str) -> tuple[bool, MainSettings | str]:
        with open(path) as fp:
            content = json.load(fp)
        return MainSettings.from_dict(content)

    @staticmethod
    def from_dict(config: dict) -> tuple[bool, MainSettings | str]:
        try:
            settings = from_dict(
                data_class=MainSettings, data=config, config=Config(cast=[Enum])
            )
        except Exception as e:
            return False, "{}: {}".format(__name__, e)

        return True, settings
