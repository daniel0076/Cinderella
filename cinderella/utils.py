import logging
from os import walk
from pathlib import Path
from typing import Iterator
from cinderella.settings import LOG_NAME


def iterate_files(path) -> Iterator[Path]:
    logger = logging.getLogger(LOG_NAME)
    for dirpath, _, filenames in walk(path):
        logger.debug(f"Current directory: {dirpath}")
        for filename in filenames:
            if filename.startswith("."):
                continue
            yield Path(dirpath, filename)
