import requests
from .constants import DEFAULT_CURRENCY_CODE, PAYPAL_ORDER_BASE_URL, construct_paypal_auth_headers


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

    return response.json()


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

    return response.json()