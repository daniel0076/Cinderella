import logging

from cinderella.beanlayer import BeanCountAPI
from cinderella.configs import Configs
from cinderella.datatypes import Transactions

LOGGER = logging.getLogger("AccountClassifier")


class AccountClassifier:
    def __init__(self):
        self.beancount_api = BeanCountAPI()
        self.configs = Configs()
        # setup default accounts
        self.configs = Configs()
        default_account = self.configs.default_accounts
        self.default_expense_account = default_account.get("expenses", "Expenses:Other")
        self.default_income_account = default_account.get("income", "Income:Other")

        # load mappings
        self.general_map = self.configs.general_map

    def classify_account(self, transactions: Transactions) -> None:
        specific_map = self.configs.get_map(transactions.source)
        pattern_maps = [self.general_map, specific_map]  # latter has higher priority

        for transaction in transactions:
            account = self._match_patterns(
                transaction, pattern_maps, self.default_expense_account
            )
            amount = transaction.postings[0].units
            self.beancount_api.create_and_add_transaction_posting(
                transaction, account, -amount.number, amount.currency
            )

    def _match_patterns(
        self, transaction, pattern_maps: list, default_account: str
    ) -> str:
        for pattern_map in pattern_maps:
            for account, keywords in pattern_map.items():
                found = self.beancount_api.find_keywords(transaction, keywords)
                if found:
                    return account
        return default_account
