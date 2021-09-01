from configs import Configs
from datatypes import Directives

import beancount.parser.parser as beancount_parser
from beancount.core.data import Transaction


class BeanCountAPI:

    def __init__(self):
        self.config = Configs()

    def write_account_bean(self, accounts: list, output_path: str):

        accounts = sorted(list(set(accounts)))

        with open(output_path, "w") as f:
            for account in accounts:
                line = f"2020-01-01 open {account}\n"
                f.write(line)

    def write_bean(self, directives: Directives, path: str):
        with open(path, "a") as f:
            for directive in directives:
                f.write(directive.to_bean())

    def read_bean(self, path: str) -> list[Transaction]:
        return beancount_parser.parse_file(path)[0]

if __name__ == "__main__":
    bc = BeanCountAPI()
    ledger = bc.read_bean("../beans/custom.bean")
    print((ledger))

