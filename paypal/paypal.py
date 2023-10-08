import enum
from dataclasses import dataclass

from django.conf import settings

import requests

# TODO: Move this to settings
PAYPAL_API_URL = "https://api.sandbox.paypal.com"
PAYPAL_ORDER_BASE_URL = f"{PAYPAL_API_URL}/v2/checkout/orders"


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
            settings.PAYPAL_CLIENT_ID,
            settings.PAYPAL_CLIENT_SECRET,
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


def create_order(
    *,
    value_usd: str,
) -> dict:
    """Create a PayPal order."""

    headers = construct_paypal_auth_headers()

    response = requests.post(
        url=PAYPAL_ORDER_BASE_URL,
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

    return response


def capture_order(
    *,
    paypal_order_id: str,
) -> dict:
    headers = construct_paypal_auth_headers()

    response = requests.post(
        url=f"{PAYPAL_ORDER_BASE_URL}/{paypal_order_id}/capture",
        headers=headers,
        # Uncomment one of these to force an error for negative testing
        # (in sandbox mode only).
        # Documentation:
        # https://developer.paypal.com/tools/sandbox/negative-testing/request-headers/
        # "PayPal-Mock-Response": '{"mock_application_codes": "INSTRUMENT_DECLINED"}'
        # "PayPal-Mock-Response": '{"mock_application_codes": "TRANSACTION_REFUSED"}'
        # "PayPal-Mock-Response": '{"mock_application_codes": "INTERNAL_SERVER_ERROR"}'
    )
    
    return response
