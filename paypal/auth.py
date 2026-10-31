import hashlib

import requests
from django.conf import settings
from django.core.cache import cache

from paypal.constants import REQUEST_TIMEOUT_S
from paypal.models import PayPalError

# Stop using a cached token this many seconds before PayPal says it expires, so
# a request never goes out with a token that is about to lapse.
TOKEN_EXPIRY_MARGIN_S = 60


def token_cache_key() -> str:
    """Cache key for the access token of the configured PayPal app.

    Includes the API URL and client ID, so switching between sandbox and live,
    or to another app, never reuses the other one's token.
    """
    app = f"{settings.PAYPAL_API_URL}|{settings.PAYPAL_CLIENT_ID}"  # type: ignore
    return f"paypal_access_token:{hashlib.sha256(app.encode()).hexdigest()}"


def get_auth_token() -> str:
    """Get an auth token from PayPal, reusing it until shortly before it expires.

    PayPal access tokens last for hours, and fetching a new one for every API
    call doubled the number of requests to PayPal.
    """
    cache_key = token_cache_key()
    cached_token = cache.get(cache_key)
    if cached_token:
        return cached_token

    # RequestException covers timeouts and connection errors as well as HTTP errors.
    try:
        response = requests.post(
            url=f"{settings.PAYPAL_API_URL}/v1/oauth2/token",
            auth=(
                settings.PAYPAL_CLIENT_ID,  # type: ignore
                settings.PAYPAL_CLIENT_SECRET,  # type: ignore
            ),  # type: ignore
            data={
                "grant_type": "client_credentials",
            },
            timeout=REQUEST_TIMEOUT_S,
        )
        response.raise_for_status()
    except requests.RequestException as e:
        raise PayPalError(e) from e

    payload = response.json()
    token = payload["access_token"]

    # Without a usable expires_in, don't guess how long the token lasts.
    try:
        lifetime_s = int(payload.get("expires_in", 0))
    except (TypeError, ValueError):
        lifetime_s = 0
    if lifetime_s > TOKEN_EXPIRY_MARGIN_S:
        cache.set(cache_key, token, lifetime_s - TOKEN_EXPIRY_MARGIN_S)

    return token


def construct_paypal_auth_headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {get_auth_token()}",
        "Content-Type": "application/json",
    }
