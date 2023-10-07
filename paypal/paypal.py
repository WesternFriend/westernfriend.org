import enum
from dataclasses import dataclass

from django.conf import settings

import requests

PAYPAL_API_URL = "https://api.sandbox.paypal.com"
PAYPAL_CREATE_ORDER_URL = f"{PAYPAL_API_URL}/v2/checkout/orders"

class CurrencyCode(enum.Enum):
    USD = "USD"

DEFAULT_CURRENCY_CODE = CurrencyCode.USD


@dataclass
class PayPalAmount:
    currency_code: CurrencyCode
    value: str


@dataclass
class PayPalPurchaseUnit:
    amount: PayPalAmount


def get_auth_token() -> str:
    """Get an auth token from PayPal."""

    response = requests.post(
        url=f"{PAYPAL_API_URL}/v1/oauth2/token",
        auth=(
            settings.PAYPAL_CLIENT_ID,
            settings.PAYPAL_CLIENT_SECRET,
        ),
        data={
            "grant_type": "client_credentials",
        },
    )

    response.raise_for_status()

    return response.json()["access_token"]


def create_order(
    *,
    value_usd: str,
) -> str:
    """Create a PayPal order."""

    headers = {
        "Authorization": f"Bearer {get_auth_token()}",
        "Content-Type": "application/json",
    }

    response = requests.post(
        url=PAYPAL_CREATE_ORDER_URL,
        headers=headers,
        json={
            "intent": "CAPTURE",
            "purchase_units": [
                {
                    "amount": {
                        "currency_code": DEFAULT_CURRENCY_CODE.value,
                        "value": value_usd,
                    },
                }
            ],
        },
    )

    response.raise_for_status()

    return response.json()["id"]
