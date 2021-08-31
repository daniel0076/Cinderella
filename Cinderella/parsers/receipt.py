import pandas as pd
from datetime import datetime
from decimal import Decimal
from typing import Union

from .base import StatementParser
from datatypes import Operation, Directive, Directives, Item
import logging

LOGGER = logging.getLogger("Receipt")


class Receipt(StatementParser):
    identifier = "receipt"
    def __init__(self):
        super().__init__()
        self.default_source_accouonts = {
            "receipt": "Assets:Cash:Wallet"
        }

    def parse(self, _: str, filepath: str) -> Directives:
        if "invos" in filepath and "csv" in filepath:
            LOGGER.debug("Using Invos specification")
            df = pd.read_csv(filepath)
            return self._parse_receipt_invos(df)

        elif "csv" in filepath:
            df = pd.read_csv(filepath, delimiter="|", skiprows=2, header=None)
            return self._parse_receipt(df)

        else:
            raise NotImplemented

    def _parse_receipt(self, records: pd.DataFrame) -> Directives:
        directives = Directives("receipt", self.identifier)

        for _, record in records.iterrows():
            if record[0] == "M":

                date = datetime.strptime(record[3], '%Y%m%d')
                title = record[5]
                amount = Decimal(record[7])
                currency = "TWD"

                directive = Directive(date, title, amount, currency)
                directive.operations.append(
                    Operation(self.default_source_accouonts["receipt"], -amount, currency)
                )
                directives.append(directive)

            elif record[0] == "D":
                # continue on last one
                item_title = record[3]
                item_price = record[2]
                directives[-1].items.append(Item(item_title, item_price))

        return directives

    def _parse_receipt_invos(self, records: pd.DataFrame) -> Directives:
        directives = Directives("receipt", self.identifier)
        prev_directive: Union[Directive, None] = None
        for _, record in records.iterrows():
            date_tw = str(record[0])
            year = int(date_tw[0:-4]) + 1911
            date_str = str(year) + str(date_tw[::-1][0:4][::-1])  # 年+月日共4位(先reverse，取4位再轉回來)

            date = datetime.strptime(date_str, "%Y%m%d")
            title = str(record["店家名稱"])
            amount = Decimal(str(record["小計"]))
            currency = "TWD"
            item_name = record["消費品項"]
            item_price = Decimal(str(record["單價"]))
            item_count = Decimal(str(record["個數"]))

            if prev_directive and prev_directive.title == title and prev_directive.date == date:
                prev_directive.amount += amount
                prev_directive.items.append(Item(f"{item_name}-{item_count} *", item_price))
            else:
                directive = Directive(date, title, amount, currency)
                directive.operations.append(
                    Operation(self.default_source_accouonts["receipt"], -amount, currency)
                )
                directive.items.append(Item(f"{item_name}-{item_count} *", item_price))
                prev_directive = directive

                directives.append(directive)

        return directives

    def _parse_card_statement(self, records: list) -> Directives:
        raise NotImplemented

    def _parse_stock_statement(self, records: list) -> Directives:
        raise NotImplemented

    def _parse_bank_statement(self, records: list) -> Directives:
        raise NotImplemented
