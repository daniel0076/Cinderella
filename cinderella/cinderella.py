import os
import logging
from pathlib import Path
from typing import Union

from cinderella.datatypes import StatementCategory
from cinderella.parsers import get_parsers
from cinderella.configs import Configs
from cinderella.classifier import AccountClassifier
from cinderella.beanlayer import BeanCountAPI
from cinderella.loader import StatementLoader, BeanLoader
from cinderella.processor import TransactionProcessor

LOGGER = logging.getLogger("Cinderella")
CURRENT_DIR = os.getcwd()


class Cinderella:
    def __init__(self, statement_path: str, output_path: Union[str, None]):

        self.parsers = self._setup_parsers()
        self.configs = Configs()
        self.bean_api = BeanCountAPI()
        self.classifier = AccountClassifier()
        self.processor = TransactionProcessor()
        self.statement_loader = StatementLoader(statement_path, self.parsers)
        self.bean_loader = BeanLoader()

        if not output_path:
            output_path = str(Path(CURRENT_DIR, self.configs.default_output))
        self.output_path = output_path

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

        accounts += configs.default_accounts.values()
        accounts += configs.general_map.keys()

        account_bean_path = str(Path(output_path, "account.bean"))
        bean_api.write_account_bean(accounts, account_bean_path)

    def _setup_parsers(self) -> list:
        parsers = []
        for parser_cls in get_parsers():
            parsers.append(parser_cls())
        return parsers

    def count_beans(self):
        transactions_group = self.statement_loader.load()

        # merge trans in receipt and card with same date and amount
        self.processor.merge_same_date_amount(
            transactions_group[StatementCategory.receipt],
            transactions_group[StatementCategory.card],
            lookback_days=3
        )

        # collect autogen list of transactions
        autogen_trans_list = [
            ts for ts_list in transactions_group.values() for ts in ts_list
        ]
        # remove transactions listed in custom and ignored bean files
        custom_transactions = self.bean_loader.load_custom_bean()
        ignored_transactions = self.bean_loader.load_ignored_bean()
        pre_defined_trans_list = [custom_transactions, ignored_transactions]
        self.processor.dedup_by_title_and_amount(
            pre_defined_trans_list, autogen_trans_list
        )

        # classify
        for transactions_list in transactions_group.values():
            for transactions in transactions_list:
                self.classifier.classify_account(transactions)

        # remove duplicated transfer transactions between banks
        self.processor.dedup_bank_transfer(autogen_trans_list, lookback_days=2)

        # output
        path = str(Path(self.output_path, "result.bean"))
        Path(path).unlink(missing_ok=True)
        for transactions_list in transactions_group.values():
            for transactions in transactions_list:
                self.bean_api.print_beans(transactions, path)
