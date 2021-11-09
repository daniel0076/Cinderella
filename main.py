import argparse
import os
import logging
from pathlib import Path

from cinderella.cinderella import Cinderella

LOGGER = logging.getLogger(__name__)
PROJECT_ROOT = os.path.dirname(__file__)
CURRENT_DIR = os.getcwd()


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Cinderella - enable automatic beancount"
    )
    parser.add_argument(
        "statements_path",
        metavar="INPUT_DIR",
        type=str,
        nargs=1,
        help="Path to statement files",
    )
    parser.add_argument(
        "output_path",
        metavar="OUTPUT_DIR",
        type=str,
        nargs="?",
        help="Path to output bean files",
    )
    parser.add_argument("-d", "--debug", help="Debug mode", action="store_true")
    parser.add_argument("-v", "--verbose", help="Verbose mode", action="store_true")
    args = parser.parse_args()

    statements_path = str(Path(CURRENT_DIR, args.statements_path[0]))
    print(f"Reading statements from {statements_path}")

    output_path = None
    if args.output_path:
        output_path = str(Path(CURRENT_DIR, args.output_path))
    print(f"Output bean files to {output_path}")

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    elif args.verbose:
        LOGGER.setLevel(level=logging.INFO)

    cinderella = Cinderella(statements_path, output_path)
    print("Processing transactions...", end="")
    cinderella.count_beans()
    print("done")
