import csv
from datatypes import Directives

class StatementParser:
    identifier = ""

    def __init__(self):
        self.parser = {
            "bank": self._parse_bank_statement,
            "card": self._parse_card_statement,
            "stock": self._parse_stock_statement,
            "receipt": self._parse_receipt
        }
        self.default_source_accounts = {}

    def parse(self, category: str, records: list[str]) -> Directives:
        records_decoded = self._decode_statement(records)
        return self.parser[category](records_decoded)

    def _decode_statement(self, raw_records: list[str]) -> list[str]:
        return raw_records

    def _parse_card_statement(self, records: list) -> Directives:
        raise NotImplemented

    def _parse_bank_statement(self, records: list) -> Directives:
        raise NotImplemented

    def _parse_stock_statement(self, records: list) -> Directives:
        raise NotImplemented

    def _parse_receipt(self, records: list) -> Directives:
        raise NotImplemented

    def _parse_price(self, raw_str: str) -> tuple:
        raise NotImplemented

    def _read_csv(self, raw_records: list[str], delimiter: str=",", quotechar: str='"', **kwargs) -> list[str]:
        records = []
        reader = csv.reader(raw_records, delimiter=delimiter, quotechar=quotechar, **kwargs)
        for row in reader:
            records.append(row)

        return records

