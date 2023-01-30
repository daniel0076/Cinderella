import pandas as pd
from datetime import datetime
from decimal import Decimal
import re
import logging

from cinderella.datatypes import Transactions, StatementType
from cinderella.parsers.base import StatementParser
from cinderella.settings import LOG_NAME

logger = logging.getLogger(LOG_NAME)


class Sinopac(StatementParser):
    identifier = "sinopac"

    def __init__(self):
        super().__init__()
        self.default_source_accounts = {
            StatementType.creditcard: "Liabilities:CreditCard:Sinopac",
            StatementType.bank: "Assets:Bank:Sinopac",
            "exchange_diff_pnl": "Income:Bank:Sinopac:ExchangeDiffPnL",
        }

    def _read_statement(self, filepath: str) -> pd.DataFrame:
        if "bank" in filepath:
            try:
                df = pd.read_csv(filepath, encoding="big5", skiprows=2)
            except UnicodeDecodeError:
                df = pd.read_csv(filepath, skiprows=2)
        else:
            df = pd.read_csv(filepath)

        df = df.replace({"\t": ""}, regex=True)
        return df

    def _parse_card_statement(self, records: list) -> Transactions:
        category = StatementType.creditcard
        transactions = Transactions(category, self.identifier)

        for _, record in records.iterrows():
            date = datetime.strptime(record[0], "%Y/%m/%d")
            title = record[3]
            price = Decimal(record[4].replace(",", ""))
            currency = "TWD"
            account = self.default_source_accounts[category]

            transaction = self.beancount_api.make_simple_transaction(
                date, title, account, -price, currency
            )
            transactions.append(transaction)

        return transactions

    def _parse_bank_statement(self, records: list) -> Transactions:
        category = StatementType.bank
        transactions = Transactions(category, self.identifier)

        for _, record in records.iterrows():
            date = datetime.strptime(record[0].lstrip().split(" ")[0], "%Y/%m/%d")
            title = record[2]
            if record[3] == " ":
                price = Decimal(record[4])
            elif record[4] == " ":
                price = -Decimal(record[3])
            else:
                raise RuntimeError(
                    f"Can not parse {self.identifier} {category.name} statement {record}"
                )

            currency = "TWD"
            account = self.default_source_accounts[category]

            # check currency exchange
            rate = Decimal(str(record[6])) if not pd.isna(record[6]) else None
            if rate:
                # xxxxxx(USD)
                try:
                    foreign_currency = re.search(r"\(([A-Z]*)\)", str(record[7])).group(
                        1
                    )
                except IndexError:
                    logger.error(
                        f"{self.identifier}: Can not determine currency for row: {record}"
                    )
                    continue

                foreign_price = self.beancount_api.make_amount(rate, currency)
                local_amount = self.beancount_api.make_amount(price, currency)
                foreign_amount = self.beancount_api.make_amount(
                    Decimal(-price / rate), foreign_currency
                )

                local_posting = self.beancount_api.make_posting(
                    account, amount=local_amount
                )
                foreign_posting = self.beancount_api.make_posting(
                    account, foreign_amount, price=foreign_price
                )
                pnl_posting = self.beancount_api.make_posting(
                    self.default_source_accounts["exchange_diff_pnl"], None
                )

                transaction = self.beancount_api.make_transaction(
                    date, title, [local_posting, foreign_posting, pnl_posting]
                )

            else:
                transaction = self.beancount_api.make_simple_transaction(
                    date, title, account, price, currency
                )

            self.beancount_api.add_transaction_comment(transaction, str(record[7]))

            transactions.append(transaction)

        return transactions
