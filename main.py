import argparse
import os
import logging
from pathlib import Path

from cinderella.parsers import get_parsers
from cinderella.configs import Configs
from cinderella.classifier import AccountClassifier
from cinderella.beanlayer import BeanCountAPI
from cinderella.loader import StatementLoader

LOGGER = logging.getLogger("Cinderella")
PROJECT_ROOT = os.path.dirname(__file__)
CURRENT_DIR = os.getcwd()


class Cinderella:
    def __init__(self, statement_path: str, output_path: str):
        self.output_path = output_path

        self.parsers = self._setup_parsers()
        self.configs = Configs()
        self.bean_api = BeanCountAPI()
        self.classifier = AccountClassifier()
        self.statement_loader = StatementLoader(statement_path, self.parsers)
        self._setup_accounts(
            self.parsers, self.configs, self.output_path, self.bean_api
        )

    def _setup_accounts(
        self, parsers: list, configs: Configs, output_path: str, bean_api: BeanCountAPI
    ):
        accounts = []

        for parser in parsers:
            accounts += parser.default_source_accounts.values()
            accounts += configs.get_map(parser.identifier).keys()

        accounts += configs.get_default_accounts().values()
        accounts += configs.get_general_map().keys()

        account_bean_path = str(Path(output_path, "account.bean"))
        bean_api.write_account_bean(accounts, account_bean_path)

    def _setup_parsers(self) -> list:
        parsers = []
        for parser_cls in get_parsers():
            parsers.append(parser_cls())
        return parsers

    def count_beans(self):

        category_transactions = self.statement_loader.load()
        self.classifier.dedup_receipt_and_payment(category_transactions)

        path = str(Path(self.output_path, "result.bean"))
        Path(path).unlink(missing_ok=True)
        for transactions_list in category_transactions.values():
            for transactions in transactions_list:
                self.classifier.classify_account(transactions)
                self.bean_api.print_beans(transactions, path)


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
    parser.add_argument("-v", "--verbose", help="Debug mode", action="store_true")
    args = parser.parse_args()

    statements_path = str(Path(CURRENT_DIR, args.statements_path[0]))
    if not args.output_path:
        output_path = str(Path(CURRENT_DIR, "beans"))
    else:
        output_path = str(Path(CURRENT_DIR, args.output_path))

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    elif args.verbose:
        logging.basicConfig(level=logging.INFO)

    cinderella = Cinderella(statements_path, output_path)
    cinderella.count_beans()
