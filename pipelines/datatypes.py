from enum import Enum


class StatementType(Enum):
    invalid = "invalid"
    ignored = "ignored"
    custom = "custom"
    bank = "bank"
    creditcard = "creditcard"
    receipt = "receipt"
    stock = "stock"
