import os
import logging
from pathlib import Path

from cinderella.datatypes import StatementCategory
from cinderella.parsers import get_parsers
from cinderella.settings import MainSettings
from cinderella.classifier import AccountClassifier
from cinderella.beanlayer import BeanCountAPI
from cinderella.loader import StatementLoader, BeanLoader
from cinderella.processor import TransactionProcessor

LOGGER = logging.getLogger(__name__)
CURRENT_DIR = os.getcwd()


class Cinderella:
    def __init__(self, settings: MainSettings):
        self.parsers = self._setup_parsers()
        self.bean_api = BeanCountAPI()
        self.classifier = AccountClassifier(settings)
        self.processor = TransactionProcessor()
        self.statement_loader = StatementLoader(
            settings.statements_directory, self.parsers
        )
        self.bean_loader = BeanLoader(settings)
        self.settings = settings

        self._setup_accounts()

    def _setup_accounts(self):
        """
        Beancount requires accounts to be declared in the bean files first.
        So we have to collect all the accounts used in Cinderella
        """
        accounts = []

        # Collect accounts from each parser
        for parser in self.parsers:
            # accounts created by each source
            accounts += parser.default_source_accounts.values()
            # accounts created by mappings of each source
            accounts += self.settings.get_mapping(parser.identifier).keys()

        # accounts created as default accounts, used when not mapping is found
        accounts += self.settings.default_accounts.values()
        # accounts created for general mapping
        accounts += self.settings.get_mapping("general").keys()

        account_bean_path = str(Path(self.settings.output_directory, "account.bean"))
        self.bean_api.write_account_bean(accounts, account_bean_path)

    def _setup_parsers(self) -> list:
        parsers = []
        for parser_cls in get_parsers():
            parsers.append(parser_cls())
        return parsers

    def count_beans(self):
        # load all the transactions group
        transactions_group = self.statement_loader.load()

        # merge trans in receipt and card with same date and amount
        self.processor.merge_same_date_amount(
            transactions_group[StatementCategory.receipt],
            transactions_group[StatementCategory.card],
            lookback_days=3,
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
        self.processor.dedup_bank_transfer(autogen_trans_list, lookback_days=5)

        # output
        path = str(Path(self.settings.output_directory, "result.bean"))
        # remove existing files
        Path(path).unlink(missing_ok=True)
        for transactions_list in transactions_group.values():
            for transactions in transactions_list:
                self.bean_api.print_beans(transactions, path)
