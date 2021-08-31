import pandas as pd
from datetime import datetime
from decimal import Decimal

from datatypes import Operation, Directive, Directives, Item
from .base import StatementParser


class Cathay(StatementParser):
    identifier = "cathay"
    def __init__(self, config: dict = {}):
        super().__init__()
        self.default_source_accounts = {
            "card": "Liabilities:CreditCard:Cathay",
            "bank": "Assets:Bank:Cathay",
        }

    def read_statement(self, filepath: str) -> pd.DataFrame:
        if "bank" in filepath:
            df = pd.read_csv(filepath, encoding="big5", skiprows=1, encoding_errors="replace")
        elif "card" in filepath:
            # 國泰帳單沒有提供年份，需由帳單第一行標題取得。可能有跨年份的問題
            with open(filepath, "r", encoding="big5") as f:
                title = f.readline()
            self.statement_year = int(title[0:3]) + 1911
            self.statement_month = str(title.split("年")[1][0:2])

            df = pd.read_csv(filepath, encoding="big5", skiprows=20, encoding_errors="replace")

        df = df.applymap(str)
        return df

    def _parse_card_statement(self, records: pd.DataFrame) -> Directives:
        directives = Directives("card", self.identifier)
        for _, record in records.iterrows():
            indicator = record["卡號末四碼"]
            if pd.isna(indicator) or not indicator.strip().isdigit():
                continue
            item_month, item_day = record[0].split("/", maxsplit=1)
            # 同上，國泰帳單，可能有跨年份的問題，一月帳單可能有去年12月的帳
            if self.statement_month == "01" and item_month == "12":
                date = datetime(year=self.statement_year-1, month=int(item_month), day=int(item_day))
            else:
                date = datetime(year=self.statement_year, month=int(item_month), day=int(item_day))

            item = record["交易說明"]
            currency = "TWD"
            amount = Decimal(record["臺幣金額"])

            directive = Directive(date, item, amount, currency)
            directive.operations.append(
                Operation(self.default_source_accounts["card"], -amount, currency)
            )

            if record["外幣金額"].strip():
                directive.items.append(Item(str(record["幣別"]), Decimal(record["外幣金額"])))

            directives.append(directive)

        return directives

    def _parse_bank_statement(self, records: pd.DataFrame) -> Directives:
        directives = Directives("bank", self.identifier)
        for _, record in records.iterrows():
            date = datetime.strptime(str(record[0]), '%Y%m%d')

            if record[2].strip():
                amount = pd.to_numeric(record[2])
                amount *= -1
            elif record[3].strip():
                amount = pd.to_numeric(record[3])
            else:
                raise RuntimeError(f"Can not parse Taiwan Post bank statement {record}")

            extra = None
            if record["備註"].strip():
                title = record["備註"]
                if record["交易資訊"].strip():
                    extra = record["交易資訊"]
            elif record["交易資訊"].strip():
                title = record["交易資訊"]
            else:
                title = record["說明"]

            currency = "TWD"
            directive = Directive(date, title, amount, currency)
            directive.operations.append(
                Operation(self.default_source_accounts["bank"], amount, currency)
            )
            directive.items.append(Item(str(record["說明"]), amount))
            if extra:
                directive.items.append(Item(str(extra)))

            directives.append(directive)

        return directives

    def _parse_price(self, raw_str: str) -> tuple:
        premise, amount_str = raw_str.split("$", maxsplit=1)
        amount = Decimal(amount_str.replace(",", ""))

        # used as expense, convert to positive
        if premise.startswith("-"):
            amount *= -1

        return (amount, "TWD")

    def _parse_stock_statement(self, records: list) -> Directives:
        raise NotImplemented
