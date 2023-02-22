from __future__ import annotations
from typing import TYPE_CHECKING, Union

if TYPE_CHECKING:
    from cinderella.settings import CinderellaSettings
    from .datatypes import Ledger, Transaction


class AccountClassifier:
    def __init__(self, settings: CinderellaSettings):
        self.settings = settings
        # setup default accounts
        default_account = settings.default_accounts
        self.default_expense_account = default_account.get("expenses", "Expenses:Other")
        self.default_income_account = default_account.get("income", "Income:Other")

        # load mappings
        self.general_map = self.settings.get_mapping("general")

    def classify_account(self, ledger: Ledger) -> None:
        source_mapping = self.settings.get_mapping(ledger.source)
        pattern_mappings = [
            source_mapping,
            self.general_map,
        ]  # former has higher priority

        for transaction in ledger.transactions:
            if len(transaction.postings) >= 2:
                continue

            account = self._match_account(transaction, pattern_mappings)
            if not account:
                account = self.default_expense_account

            amount = transaction.postings[0].amount
            transaction.create_and_append_posting(
                account, -amount.quantity, amount.currency
            )

    def _match_account(
        self, transaction: Transaction, pattern_mappings: list
    ) -> Union[None, str]:
        for pattern_map in pattern_mappings:
            for account, keywords in pattern_map.items():
                found = transaction.grep(keywords)
                if found:
                    return account
        return None
