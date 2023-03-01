from pathlib import Path

from cinderella.settings import CinderellaSettings
from cinderella.ledger import utils as ledger_util
from cinderella.ledger.classifier import TransactionClassifier
from cinderella.ledger.datatypes import Ledger, StatementType
from cinderella.statement.loader import StatementLoader
from cinderella.external import beancountapi


class Cinderella:
    def __init__(self, settings: CinderellaSettings):
        self.settings = settings
        self.statement_loader = StatementLoader()
        self.classifier = TransactionClassifier(settings)

    def _collect_accounts(self) -> list:
        accounts = []
        # accounts created as default accounts, used when not mapping is found
        accounts += self.settings.default_accounts.values()
        # accounts created for mapping
        for mapping in self.settings.mappings.values():
            accounts += mapping.keys()  # keys are the accounts
        # accounts created from each statement parsers
        accounts += self.statement_loader.get_all_statement_accounts()

        return accounts

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
            beancountapi.load_beanfile_to_internal_transactions(
                self.settings.beancount_settings.overwrite_beanfiles_folder,
            )
        )
        ignored_ledger = Ledger("ignored_ledger", StatementType.custom)
        ignored_ledger.transactions = (
            beancountapi.load_beanfile_to_internal_transactions(
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

        """
        Beancount requires accounts to be declared in the bean files first.
        So we have to collect all the accounts used in Cinderella
        """
        accounts_beanfile = Path(
            self.settings.beancount_settings.output_beanfiles_folder, "account.bean"
        )
        accounts = self._collect_accounts()
        beancountapi.write_accounts_to_beanfile(accounts, accounts_beanfile.as_posix())

        # output
        path = (
            Path(self.settings.beancount_settings.output_beanfiles_folder)
            / "result.bean"
        )
        # remove existing files
        path.unlink(missing_ok=True)

        for ledgers in ledgers_by_type.values():
            for transaction in ledgers:
                beancountapi.print_beans(transaction, path.as_posix())
