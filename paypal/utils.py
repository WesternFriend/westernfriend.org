import enum
from dataclasses import dataclass

from django.conf import settings

import requests

from paypal.constants import PAYPAL_API_URL



class PayPalError(Exception):
    pass


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
            settings.PAYPAL_CLIENT_ID,  # type: ignore
            settings.PAYPAL_CLIENT_SECRET,  # type: ignore
        ),  # type: ignore
        data={
            "grant_type": "client_credentials",
        },
    )

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        raise PayPalError(e)

    return response.json()["access_token"]


def construct_paypal_auth_headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {get_auth_token()}",
        "Content-Type": "application/json",
    }
