import enum
from dataclasses import dataclass


class PayPalError(Exception):
    pass


class CurrencyCode(enum.Enum):
    USD = "USD"


@dataclass
class PayPalAmount:
    currency_code: CurrencyCode
    value: str


@dataclass
class PayPalPurchaseUnit:
    amount: PayPalAmount
