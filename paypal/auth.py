import requests
from django.conf import settings

from paypal.models import PayPalError


def get_auth_token() -> str:
    """Get an auth token from PayPal."""

    response = requests.post(
        url=f"{settings.PAYPAL_API_URL}/v1/oauth2/token",
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
