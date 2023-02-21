import pandas as pd
from datetime import datetime
from decimal import Decimal

from cinderella.statement.datatypes import Transactions, StatementType
from cinderella.parsers.base import StatementParser


class Cathay(StatementParser):
    identifier = "cathay"

    def __init__(self):
        super().__init__()
        self.default_source_accounts = {
            StatementType.creditcard: "Liabilities:CreditCard:Cathay",
            StatementType.bank: "Assets:Bank:Cathay",
        }

    def _read_statement(self, filepath: str) -> pd.DataFrame:
        if StatementType.bank.name in filepath:
            df = pd.read_csv(
                filepath, encoding="big5", skiprows=1, encoding_errors="replace"
            )
        elif StatementType.creditcard.name in filepath:
            # 國泰帳單沒有提供年份，需由帳單第一行標題取得。可能有跨年份的問題
            with open(filepath, "r", encoding="big5") as f:
                title = f.readline()
            self.statement_year = int(title[0:3]) + 1911
            self.statement_month = str(title.split("年")[1][0:2])

            df = pd.read_csv(
                filepath, encoding="big5", skiprows=20, encoding_errors="replace"
            )

        return df

    def _parse_card_statement(self, records: pd.DataFrame) -> Transactions:
        category = StatementType.creditcard
        transactions = Transactions(category, self.identifier)

        for _, record in records.iterrows():
            indicator = record["卡號末四碼"]
            if pd.isna(indicator) or not indicator.strip().isdigit():
                continue

            item_month, item_day = record[0].split("/", maxsplit=1)
            # 處理可能有跨年份的問題，1月帳單可能有去年12月的帳
            if self.statement_month == "01" and item_month == "12":
                date = datetime(
                    year=self.statement_year - 1,
                    month=int(item_month),
                    day=int(item_day),
                )
            else:
                date = datetime(
                    year=self.statement_year, month=int(item_month), day=int(item_day)
                )

            title = record["交易說明"].strip()
            currency = "TWD"
            price = Decimal(record["臺幣金額"])
            account = self.default_source_accounts[category]

            transaction = self.beancount_api.make_simple_transaction(
                date, title, account, -price, currency
            )
            transactions.append(transaction)

            if record["外幣金額"].strip():
                self.beancount_api.add_transaction_comment(
                    transaction, f"{record['幣別']}-{record['外幣金額']}"
                )

        return transactions

    def _parse_bank_statement(self, records: pd.DataFrame) -> Transactions:
        category = StatementType.bank
        transactions = Transactions(category, self.identifier)
        for _, record in records.iterrows():
            date = datetime.strptime(str(record[0]), "%Y%m%d")

            if str(record[2]).strip():  # 轉出
                price = Decimal(record[2])
                price *= -1
            elif str(record[3]).strip():  # 轉入
                price = Decimal(record[3])
            else:
                raise RuntimeError(
                    f"Can not parse {self.identifier} {category.name} statement {record}"
                )

            comment = str(record["備註"]).lstrip() if not pd.isna(record["備註"]) else ""
            explanation = str(record["說明"])
            info = str(record["交易資訊"]).lstrip()

            if comment:
                title = comment
                extra = f"{explanation} {info}"
            else:
                title = info
                extra = explanation

            currency = "TWD"
            account = self.default_source_accounts[category]
            transaction = self.beancount_api.make_simple_transaction(
                date, title, account, price, currency
            )
            self.beancount_api.add_transaction_comment(transaction, extra)

            transactions.append(transaction)

        return transactions
