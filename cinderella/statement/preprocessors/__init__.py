import logging
from pathlib import Path
import os

from cinderella.settings import LOG_NAME, StatementSettings
from .einvoice import Einvoice
from .richart import Richart
from .esun import ESun


class StatementPreprocessor:
    def __init__(self, settings: StatementSettings):
        self.logger = logging.getLogger(LOG_NAME)
        self.settings = settings
        self.logger.debug(f"Preprocessor settings:\n{settings}")

        # create processor objects according to config
        preprocessor_cls = [Einvoice, Richart, ESun]
        self.preprocessors = {}
        for c in preprocessor_cls:
            self.preprocessors[c.source_name] = c(settings)

    def process(self):
        if self.settings.raw_statement_folder == "":
            return

        input_folder = Path(self.settings.raw_statement_folder)

        # walk the directory tree and find all statements
        for dirpath, _, filenames in os.walk(input_folder):
            # ignore hidden files
            files = [
                Path(dirpath, filename)
                for filename in filenames
                if not filename.startswith(".")
            ]

            # N^2 complexity here to allow putting source_name at any part of the file path
            for file in files:
                for source_name, processor in self.preprocessors.items():
                    if source_name not in file.as_posix():
                        continue

                    print(
                        f"preprocessor[{source_name}]: {file.relative_to(input_folder)}"
                    )
                    result = processor.process(file)
                    if not result.success:
                        self.logger.error(result.message)
