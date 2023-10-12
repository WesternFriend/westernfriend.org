import enum
from dataclasses import dataclass

from django.conf import settings
from django.core.cache import cache

import requests

# TODO: Move this to settings
PAYPAL_API_URL = "https://api.sandbox.paypal.com"
PAYPAL_ORDER_BASE_URL = f"{PAYPAL_API_URL}/v2/checkout/orders"
PAYPAL_SUBSCRIPTIONS_BASE_URL = f"{PAYPAL_API_URL}/v1/billing/subscriptions"

ONE_DAY_S = 60 * 60 * 24 # 24 hours

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


def get_subscription(
    *,
    paypal_subscription_id: str,
) -> dict:
    headers = construct_paypal_auth_headers()

    response = requests.get(
        url=f"{PAYPAL_SUBSCRIPTIONS_BASE_URL}/{paypal_subscription_id}",
        headers=headers,
    )

    return response.json()


def subscription_is_active(
    *,
    paypal_subscription_id: str,
) -> bool:
    """Check the status of a PayPal subscription."""
    # Check the cache first
    cache_key = f"paypal_subscription_{paypal_subscription_id}"
    status = cache.get(cache_key)

    if status is None:
        subscription = get_subscription(
            paypal_subscription_id=paypal_subscription_id,
        )

        status = subscription["status"]

        # Cache the status for one day
        cache.set(
            cache_key,
            status,
            ONE_DAY_S,  # 24 hours
        )


    return status == "ACTIVE"