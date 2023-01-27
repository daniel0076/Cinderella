import argparse
import os
import logging

from cinderella.cinderella import Cinderella
from cinderella.settings import CinderellaSettings

LOGGER = logging.getLogger(__name__)
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

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    elif args.verbose:
        LOGGER.setLevel(level=logging.INFO)

    # create configuration object
    success, value = CinderellaSettings.from_file(args.config)
    if not success:
        LOGGER.error(value)
        exit(1)
    settings: CinderellaSettings = value

    LOGGER.debug(f"Cinderella configurations:\n{settings}")
    LOGGER.info(f"Reading statements from: {settings.statement_settings.ready_statement_folder}")
    LOGGER.info(f"Output beanfiles to: {settings.beancount_settings.output_beanfiles_folder}")
    print()

    cinderella = Cinderella(settings)
    print("Processing transactions...", end="")
    cinderella.count_beans()
    print("done")
