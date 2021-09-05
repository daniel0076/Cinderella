from datatypes import Transactions
import logging

from beanlayer import BeanCountAPI

from configs import Configs

LOGGER = logging.getLogger("AccountClassifier")


class AccountClassifier:
    def __init__(self):
        self.beancount_api = BeanCountAPI()
        self.configs = Configs()
        # setup default accounts
        settings = self.configs.get_settings()
        default_account = settings.get("default_accounts", {})
        self.default_expense_account = default_account.get("expenses", "Expenses:Other")
        self.default_income_account = default_account.get("income", "Income:Other")

        # load mappings
        self.general_map = self.configs.get_general_map()

    def classify_account(self, transactions: Transactions) -> None:
        specific_map = self.configs.get_map(transactions.source)
        pattern_maps = [self.general_map, specific_map]  # latter has higher priority

        for transaction in transactions:
            account = self._match_patterns(
                transaction, pattern_maps, self.default_expense_account
            )
            self.beancount_api.create_and_add_transaction_posting(transaction, account)

    def dedup_receipt_and_payment(
        self, category_map: dict[str, list[Transactions]]
    ) -> None:
        primary_group = "receipt"
        primary_transactions_list = category_map.pop(primary_group, [])

        for other_transactions_list in category_map.values():
            for other_transactions in other_transactions_list:
                for primary_transactions in primary_transactions_list:
                    self.beancount_api.merge_duplicated_transactions(
                        other_transactions, primary_transactions
                    )
        category_map[primary_group] = primary_transactions_list

    def _match_patterns(
        self, transaction, pattern_maps: list, default_account: str
    ) -> str:
        for pattern_map in pattern_maps:
            for account, keywords in pattern_map.items():
                found = self.beancount_api.find_keywords(transaction, keywords)
                if found:
                    return account
        return default_account
