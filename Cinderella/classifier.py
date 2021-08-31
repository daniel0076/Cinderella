from datatypes import Directive, Directives, Operation, Item
from configs import Configs
import logging

LOGGER = logging.getLogger("AccountClassifier")

class AccountClassifier:
    def __init__(self):
        self.configs = Configs()
        # setup default accounts
        settings = self.configs.get_settings()
        default_account = settings.get('default_accounts', {})
        self.default_expense_account = default_account.get('expenses', "Expenses:Other")
        self.default_income_account = default_account.get('income', "Income:Other")

        # load mappings
        self.general_map = self.configs.get_general_map()

    def classify_account_by_keyword(self, directives: Directives) -> None:
        specific_map = self.configs.get_map(directives.source)
        for directive in directives:
            found = self._find_by_title_and_items(directive, specific_map)
            if not found:
                found = self._find_by_title_and_items(directive, self.general_map)
            if not found:
                directive.operations.append(Operation(self.default_expense_account))

    def _find_by_title_and_items(self, directive: Directive, keyword_map) -> bool:
        for account, keywords in keyword_map.items():
            if not isinstance(keywords, list):
                LOGGER.error("Malformed keyword map, values should be a list %s", keywords)
                continue
            for keyword in keywords:
                if keyword in directive.title:
                    directive.operations.append(Operation(account))
                    return True
                for item in directive.items:
                    if keyword in item.title:
                        directive.operations.append(Operation(account))
                        return True
        return False

    def union_directives(self, directives_groups: dict) -> list:
        primary_record = "receipt"
        record_union = []
        record_union += directives_groups.pop(primary_record, [])

        # build map for faster match
        price_date_match = {}
        for record in record_union:
            price_date_match[(record.date, record.amount)] = record

        for category, directives in directives_groups.items():
            for directive in directives:
                key = (directive.date, directive.amount)
                prime_directive = price_date_match.get(key)
                if prime_directive:  # the primary record exists
                    prime_directive.operations = directive.operations
                    prime_directive.items.append(Item(f"Payment: {directive.title}", directive.amount))
                else:
                    record_union.append(directive)
        return record_union



