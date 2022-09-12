import pandas as pd
from datetime import datetime
from decimal import Decimal

from cinderella.datatypes import Transactions, StatementCategory
from cinderella.parsers.base import StatementParser


class Schwab(StatementParser):
    identifier = "schwab"

    def __init__(self):
        super().__init__()
        self.default_source_accounts = {
            StatementCategory.stock: "Assets:Stock:Schwab",
            StatementCategory.bank: "Assets:Bank:Schwab",
            "pnl_account": "Income:Stock:Schwab:PnL",
            "fees_account": "Expenses:Stock:Schwab:Fees",
        }

    def _read_statement(self, filepath: str) -> pd.DataFrame:
        df = pd.read_csv(
            filepath,
            skiprows=1,
            encoding_errors="replace",
            skipfooter=1,
            engine="python",
        )
        return df

    def _parse_card_statement(self, records: pd.DataFrame) -> Transactions:
        raise NotImplementedError

    def _parse_bank_statement(self, records: pd.DataFrame) -> Transactions:
        raise NotImplementedError

    def _parse_stock_statement(self, records: pd.DataFrame) -> Transactions:
        transactions = Transactions(StatementCategory.stock, self.identifier)
        stock_account = self.default_source_accounts[StatementCategory.stock]
        bank_account = self.default_source_accounts[StatementCategory.bank]
        pnl_account = self.default_source_accounts["pnl_account"]
        fees_account = self.default_source_accounts["fees_account"]

        for _, record in records.iterrows():
            date = datetime.strptime(str(record["Date"]), "%m/%d/%Y")
            action = record["Action"]
            symbol = record["Symbol"]
            quantity = (
                Decimal(str(record["Quantity"]))
                if not pd.isna(record["Quantity"])
                else Decimal("0")
            )
            quantity = -quantity if action == "Sell" else quantity
            price = (
                Decimal(record["Price"].replace("$", ""))
                if not pd.isna(record["Price"])
                else Decimal("0")
            )
            fees = (
                -Decimal(record["Fees & Comm"].replace("$", ""))
                if not pd.isna(record["Fees & Comm"])
                else Decimal("0")
            )
            total = Decimal(record["Amount"].replace("$", ""))
            title = (
                f"{action} {quantity} {symbol}" if quantity else f"{action} {symbol}"
            )

            if not pd.isna(symbol):
                cost = None
                trade_price = None
                if price:
                    if action == "Sell":
                        cost = self.beancount_api.make_cost(None, None, None)
                        trade_price = self.beancount_api.make_amount(price, "USD")
                    else:
                        cost = self.beancount_api.make_cost(price, "USD", date.date())

                trade_amount = self.beancount_api.make_amount(quantity, symbol)
                cash_amount = self.beancount_api.make_amount(total, "USD")
                trade_posting = self.beancount_api.make_posting(
                    stock_account, trade_amount, cost=cost, price=trade_price
                )
                balance_posting = self.beancount_api.make_posting(
                    bank_account, cash_amount
                )
                fees_posting = self.beancount_api.make_simple_posting(
                    fees_account, fees, "USD"
                )
                pnl_posting = self.beancount_api.make_posting(pnl_account, None)
                t = self.beancount_api.make_transaction(
                    date,
                    title,
                    [trade_posting, balance_posting, fees_posting, pnl_posting],
                )
                transactions.append(t)
            else:
                continue

        return transactions
