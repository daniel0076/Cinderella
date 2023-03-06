from __future__ import annotations
from typing import TYPE_CHECKING, Union

from cinderella.ledger.datatypes import Posting, TransactionFlag

if TYPE_CHECKING:
    from cinderella.settings import CinderellaSettings
    from .datatypes import Ledger, Transaction


class TransactionClassifier:
    def __init__(self, settings: CinderellaSettings):
        self.settings = settings
        # setup default accounts
        default_account = settings.default_accounts
        self.default_expense_account = default_account.get("expenses", "Expenses:Other")
        self.default_income_account = default_account.get("income", "Income:Other")
        self.conversion_diff_account = default_account.get(
            "conversion_diff", "Income:PnL:ConversionDiffs"
        )

        # load mappings
        self.general_map = self.settings.get_mapping("general")

    def classify_account(self, ledger: Ledger) -> None:
        source_mapping = self.settings.get_mapping(ledger.source)
        pattern_mappings = [
            source_mapping,
            self.general_map,
        ]  # former has higher priority

        for transaction in ledger.transactions:
            if transaction.flag == TransactionFlag.CONVERSIONS:
                transaction.postings.append(Posting(self.conversion_diff_account, None))
                continue

            if len(transaction.postings) >= 2:
                continue

            account = self._match_account(transaction, pattern_mappings)
            if not account:
                account = self.default_expense_account

            # currency conversion if there is a price, add a posting with account only
            if transaction.postings[0].price:
                transaction.append_postings(Posting(account, None))
            else:
                amount = transaction.postings[0].amount
                if amount:
                    transaction.create_and_append_posting(
                        account, -amount.quantity, amount.currency
                    )
                else:
                    transaction.append_postings(Posting(account, None))

    def _match_account(
        self, transaction: Transaction, pattern_mappings: list
    ) -> Union[None, str]:
        for pattern_map in pattern_mappings:
            for account, keywords in pattern_map.items():
                found = transaction.grep(keywords)
                if found:
                    return account
        return None
