import pandas as pd
from datetime import datetime
from decimal import Decimal

from cinderella.datatypes import Transactions, StatementCategory
from cinderella.parsers.base import StatementParser


class ESun(StatementParser):
    identifier = "esun"

    def __init__(self, config: dict = {}):
        super().__init__()
        self.default_source_accounts = {
            StatementCategory.bank: "Assets:Bank:ESun",
        }

    def _read_statement(self, filepath: str) -> pd.DataFrame:
        df = pd.read_excel(filepath, skiprows=9, skipfooter=3, thousands=",")
        return df

    def _parse_card_statement(self, records: pd.DataFrame) -> Transactions:
        raise NotImplementedError

    def _parse_bank_statement(self, records: pd.DataFrame) -> Transactions:
        category = StatementCategory.bank
        transactions = Transactions(category, self.identifier)

        for _, record in records.iterrows():
            date = record["交易日期"]
            if isinstance(record["交易日期"], str):
                # Some column has *
                date = datetime.strptime(date[1:], "%Y/%m/%d")

            if not pd.isna(record["提"]):
                price = Decimal(str(record["提"]))
                price *= -1
            elif not pd.isna(record["存"]):
                price = Decimal(str(record["存"]))
            else:
                raise RuntimeError(
                    f"Can not parse {self.identifier} {category.name} statement {record}"
                )

            title = str(record["摘要"])
            currency = "TWD"
            account = self.default_source_accounts[category]

            transaction = self.beancount_api.make_simple_transaction(
                date, title, account, price, currency
            )

            comment = ""
            if not pd.isna(record["備註"]):
                comment += str(record["備註"])
            if not pd.isna(record["對方銀行代碼/帳號"]):
                comment += " " + str(record["對方銀行代碼/帳號"])

            if comment:
                self.beancount_api.add_transaction_comment(transaction, comment)

            transactions.append(transaction)

        return transactions

    def _parse_price(self, raw_str: str) -> tuple:
        premise, price_str = raw_str.split("$", maxsplit=1)
        price = Decimal(price_str.replace(",", ""))

        # used as expense, convert to positive
        if premise.startswith("-"):
            price *= -1

        return (price, "TWD")

    def _parse_stock_statement(self, records: list) -> Transactions:
        raise NotImplementedError
