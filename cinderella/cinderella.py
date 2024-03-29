from pathlib import Path

from cinderella.datatypes import StatementType
from cinderella.parsers import get_parsers
from cinderella.settings import CinderellaSettings
from cinderella.classifier import AccountClassifier
from cinderella.beanlayer import BeanCountAPI
from cinderella.loader import StatementLoader, BeanLoader
from cinderella.transaction import TransactionProcessor


class Cinderella:
    def __init__(self, settings: CinderellaSettings):
        self.parsers = self._setup_parsers()
        self.bean_api = BeanCountAPI()
        self.classifier = AccountClassifier(settings)
        self.processor = TransactionProcessor()
        self.statement_loader = StatementLoader(
            settings.statement_settings.ready_statement_folder, self.parsers
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

        account_bean_path = str(
            Path(
                self.settings.beancount_settings.output_beanfiles_folder, "account.bean"
            )
        )
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
            transactions_group[StatementType.receipt]
            + transactions_group[StatementType.creditcard],
            lookback_days=3,
        )

        # collect autogen list of transactions
        autogen_trans_list = [
            ts for ts_list in transactions_group.values() for ts in ts_list
        ]
        # remove transactions listed in custom and ignored bean files
        custom_transactions = self.bean_loader.load_beanfile_as_transactions(
            self.settings.beancount_settings.overwrite_beanfiles_folder,
            StatementType.custom,
        )
        ignored_transactions = self.bean_loader.load_beanfile_as_transactions(
            self.settings.beancount_settings.ignored_beanfiles_folder,
            StatementType.ignored,
        )
        pre_defined_trans_list = [custom_transactions, ignored_transactions]
        self.processor.dedup_by_title_and_amount(
            pre_defined_trans_list + autogen_trans_list
        )

        # classify
        for transactions_list in transactions_group.values():
            for transactions in transactions_list:
                self.classifier.classify_account(transactions)

        # remove duplicated transfer transactions between banks
        self.processor.dedup_bank_transfer(
            autogen_trans_list,
            lookback_days=self.settings.ledger_processing_settings.transfer_matching_days,
        )

        # output
        path = (
            Path(self.settings.beancount_settings.output_beanfiles_folder)
            / "result.bean"
        )
        # remove existing files
        path.unlink(missing_ok=True)
        for transactions_list in transactions_group.values():
            for transactions in transactions_list:
                self.bean_api.print_beans(transactions, path.as_posix())
