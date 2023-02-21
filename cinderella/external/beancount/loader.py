import logging
from typing import Iterator, Union
from os import walk, getcwd
from pathlib import Path
from collections import defaultdict

from cinderella.parsers.base import StatementParser
from cinderella.statement.datatypes import Transactions, StatementType
from cinderella.external.beancount.utils import BeanCountAPI
from cinderella.settings import CinderellaSettings, LOG_NAME

logger = logging.getLogger(LOG_NAME)
CURRENT_DIR = getcwd()


class BeanLoader:
    def __init__(self, settings: CinderellaSettings):
        self.settings = settings
        self.beancount_api = BeanCountAPI()

    def load_beanfile_as_transactions(
        self, path: Path | str, category: StatementType
    ) -> Transactions:
        transactions = Transactions(category, category.name)
        logger.debug(f"===Loading beanfiles: {category.name}===")
        for dirpath, _, filenames in walk(path):
            logger.debug(f"Current directory {dirpath}")
            for filename in filenames:
                path = Path(dirpath, filename)
                logger.debug(f"Loading beanfile: {filename}")

                entries = self.beancount_api._load_bean(path.as_posix())
                transactions.extend(entries)

        return transactions
