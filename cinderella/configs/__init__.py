import os
import json
from os.path import dirname, realpath
from pathlib import Path
import logging

LOGGER = logging.getLogger(__name__)


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class Configs(metaclass=Singleton):
    def __init__(self):
        self.current_dir = dirname(realpath(__file__))
        self._check_mappings()

        config_path = Path(self.current_dir, "settings.json")
        with open(config_path) as f:
            self.settings = json.load(f)

    def _check_mappings(self):
        mapping_path = Path(self.current_dir, "mappings")
        sample_mapping_path = Path(self.current_dir, "mappings.sample")
        if not os.path.exists(mapping_path):
            try:
                os.rename(sample_mapping_path, mapping_path)
                LOGGER.info("configs/mappings not found, create with mappings.sample")
            except (OSError, IsADirectoryError, NotADirectoryError):
                LOGGER.error(
                    "Failed to create mappings, check the configs/mappings directory"
                )
                raise RuntimeError

    @property
    def default_accounts(self) -> dict:
        return self.settings["default_accounts"]

    @property
    def default_output(self) -> str:
        return self.settings["default_output"]

    @property
    def custom_bean_keyword(self) -> str:
        return self.settings["custom_bean_keyword"]

    @property
    def ignored_bean_keyword(self) -> str:
        return self.settings["ignored_bean_keyword"]

    @property
    def general_map(self) -> dict:
        map_path = Path(self.current_dir, "mappings/general.json")
        with open(map_path) as f:
            mappings = json.load(f)
        return mappings

    def get_map(self, name: str) -> dict:
        path = Path(self.current_dir, f"mappings/{name}.json")
        if not os.path.exists(path):
            return {}

        with open(path) as f:
            mappings = json.load(f)
        return mappings
