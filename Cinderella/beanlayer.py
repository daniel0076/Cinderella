from configs import Configs
from datatypes import Directives


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
