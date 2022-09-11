import argparse
import os
import logging

from cinderella.cinderella import Cinderella
from cinderella.settings import MainSettings

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

    # create configuration object
    success, value = MainSettings.from_file(args.config)
    if not success:
        LOGGER.error(value)
        exit(1)
    settings: MainSettings = value

    print("Cinderella configurations:")
    print(f"Reading statements from: {settings.statements_directory}")
    print(f"Output bean files to: {settings.output_directory}")
    print()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    elif args.verbose:
        LOGGER.setLevel(level=logging.INFO)

    cinderella = Cinderella(settings)
    print("Processing transactions...", end="")
    cinderella.count_beans()
    print("done")
