import argparse
import os
import logging
from collections import defaultdict
from typing import Union
from pathlib import Path

from datatypes import Statement, Directives
from parsers import get_parsers
from configs import Configs
from classifier import AccountClassifier
from beanlayer import BeanCountAPI
from loader import StatementLoader

LOGGER = logging.getLogger("Cinderella")
PROJECT_ROOT = os.path.dirname(__file__)
CURRENT_DIR = os.getcwd()


class Cinderella:
    def __init__(self, statement_path: str, output_path: str):
        self.parsers = []
        self.configs = Configs()
        self.bean_api = BeanCountAPI()
        self.classifier = AccountClassifier()
        self.loader = StatementLoader(statement_path)
        self.output_path = output_path

        self.setup()

    def setup(self):
        # for gen account beans
        accounts = []

        for parser_cls in get_parsers():
            obj = parser_cls()
            self.parsers.append({"identifier": parser_cls.identifier, "object": obj})

            accounts += obj.default_source_accounts.values()
            accounts += self.configs.get_map(parser_cls.identifier).keys()

        accounts += self.configs.get_default_accounts().values()
        accounts += self.configs.get_general_map().keys()

        account_bean_path = str(Path(self.output_path, "account.bean"))
        self.bean_api.write_account_bean(accounts, account_bean_path)

    def count_beans(self):
        directives_groups = defaultdict(list)
        for statement in self.loader.load_statements():
            directives = self._parse_statement(statement)
            if directives:
                self.classifier.classify_account_by_keyword(directives)
                directives_groups[directives.category] += directives

        records = self._union_directives(directives_groups)
        path = str(Path(self.output_path, "result.bean"))
        self.bean_api.write_bean(records, path)

    def _parse_statement(self, statement: Statement) -> Union[None, Directives]:
        # find suitable parser by filename identifier
        parser = None
        for parser_it in self.parsers:
            if parser_it["identifier"] in statement.filename:
                parser = parser_it["object"]

        if not parser:
            LOGGER.error("No parser found for statement file: %s", statement.filename)
            return None

        directives = parser.parse(statement.category, statement.records)

        return directives

    def _union_directives(self, directives_groups: dict, update_account: bool=True) -> list:
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
                if key in price_date_match:  # the primary record exists
                    if update_account:
                        price_date_match[key].operations = directive.operations
                else:
                    record_union.append(directive)
        return record_union

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description="Cinderella - enable automatic beancount")
    parser.add_argument("statements_path", metavar='INPUT_DIR', type=str, nargs=1,
                        help="Path to statement files")
    parser.add_argument("output_path", metavar='OUTPUT_DIR', type=str, nargs="?",
                        help="Path to output bean files")
    args = parser.parse_args()

    statements_path = str(Path(CURRENT_DIR, args.statements_path[0]))
    if not args.output_path:
        output_path = str(Path(CURRENT_DIR, "beans"))
    else:
        output_path = str(Path(CURRENT_DIR, args.output_path))


    cinderella = Cinderella(statements_path, output_path)
    cinderella.count_beans()


