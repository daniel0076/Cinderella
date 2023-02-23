from pathlib import Path

from cinderella.statement.datatypes import StatementType
from cinderella.settings import CinderellaSettings
from cinderella.ledger import utils as ledger_util
from cinderella.ledger.classifier import TransactionClassifier
from cinderella.ledger.datatypes import Ledger
from cinderella.statement.loader import StatementLoader
from cinderella.external.beancountapi import BeanCountAPI


class Cinderella:
    def __init__(self, settings: CinderellaSettings):
        self.settings = settings
        self.bean_api = BeanCountAPI()
        self.statement_loader = StatementLoader()
        self.classifier = TransactionClassifier(settings)

        self._setup_accounts()

    def _setup_accounts(self):
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

    def count_beans(self):
        # load all the ledgers by statment type
        ledgers_by_type = self.statement_loader.load(
            self.settings.statement_settings.ready_statement_folder
        )

        # merge trans in receipt and card with same date and amount
        ledger_util.merge_same_date_amount(
            ledgers_by_type[StatementType.receipt]
            + ledgers_by_type[StatementType.creditcard],
            tolerance_days=3,
        )

        # remove transactions found ledgers marked ignored and overwrite
        overwritten_ledger = Ledger("overwritten_ledger", StatementType.custom)
        overwritten_ledger.transactions = (
            self.bean_api.load_beanfile_to_internal_transactions(
                self.settings.beancount_settings.overwrite_beanfiles_folder,
            )
        )
        ignored_ledger = Ledger("ignored_ledger", StatementType.custom)
        ignored_ledger.transactions = (
            self.bean_api.load_beanfile_to_internal_transactions(
                self.settings.beancount_settings.ignored_beanfiles_folder
            )
        )

        all_parsed_ledgers = []
        for ledgers in ledgers_by_type.values():
            all_parsed_ledgers.extend(ledgers)

        ledger_util.dedup_by_title_and_amount(
            [*all_parsed_ledgers, overwritten_ledger, ignored_ledger]
        )

        # classify
        for ledgers in ledgers_by_type.values():
            for ledger in ledgers:
                self.classifier.classify_account(ledger)

        """
        remove duplicated transfer transactions between banks,
        this can only be done after classification
        """
        ledger_util.dedup_bank_transfer(
            ledgers_by_type[StatementType.bank],
            tolerance_days=self.settings.ledger_processing_settings.transfer_matching_days,
        )

        # output
        path = (
            Path(self.settings.beancount_settings.output_beanfiles_folder)
            / "result.bean"
        )
        # remove existing files
        path.unlink(missing_ok=True)

        """
        Beancount requires accounts to be declared in the bean files first.
        So we have to collect all the accounts used in Cinderella
        """
        accounts = []

        # Collect accounts from each parser

        for ledgers in ledgers_by_type.values():
            for transaction in ledgers:
                self.bean_api.print_beans(transaction, path.as_posix())
