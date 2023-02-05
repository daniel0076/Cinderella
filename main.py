import argparse
import os
import logging

from cinderella.cinderella import Cinderella
from cinderella.settings import CinderellaSettings, LOG_NAME
from cinderella.preprocessor import StatementPreprocessor

PROJECT_ROOT = os.path.dirname(__file__)
CURRENT_DIR = os.getcwd()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Cinderella - enable automatic beancount"
    )
    parser.add_argument(
        "-c",
        "--config",
        metavar="/path/to/config",
        required=True,
        help="Path to the config file",
    )
    parser.add_argument("-d", "--debug", help="Debug mode", action="store_true")
    parser.add_argument("-v", "--verbose", help="Verbose mode", action="store_true")
    args = parser.parse_args()

    # set up logger
    logger = logging.getLogger(LOG_NAME)
    if args.debug:
        logger.setLevel(logging.DEBUG)
    elif args.verbose:
        logger.setLevel(logging.INFO)
    # create console handler and set level to debug
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter("[%(levelname)s] %(message)s")
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # create configuration object
    success, value = CinderellaSettings.from_file(args.config)
    if not success:
        logger.error(value)
        exit(1)
    settings: CinderellaSettings = value

    logger.debug(f"Configurations details:\n{settings}")
    print("Configurations: ")
    print(
        f"Preprocessing statements from: {settings.statement_settings.raw_statement_folder}"
    )
    print(
        f"Reading statements from: {settings.statement_settings.ready_statement_folder}"
    )
    print(f"Output beanfiles to: {settings.beancount_settings.output_beanfiles_folder}")

    # create statement preprocessor
    print("Preprocessing raw statements")
    statement_preprocessor = StatementPreprocessor(settings.statement_settings)
    statement_preprocessor.process()

    print("Processing statements to transactions...", end="")
    cinderella = Cinderella(settings)
    cinderella.count_beans()
    print("done")
