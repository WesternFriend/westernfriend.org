import logging

import requests
from django.core.cache import cache
from requests.exceptions import RequestException

from paypal.constants import (
    ONE_DAY_S,
    PAYPAL_SUBSCRIPTIONS_BASE_URL,
    REQUEST_TIMEOUT_S,
)
from paypal.models import PayPalError

from .auth import construct_paypal_auth_headers

logger = logging.getLogger(__name__)


def get_subscription(
    *,
    paypal_subscription_id: str,
) -> dict:
    headers = construct_paypal_auth_headers()

    # RequestException covers timeouts and connection errors as well as HTTP errors.
    try:
        response = requests.get(
            url=f"{PAYPAL_SUBSCRIPTIONS_BASE_URL}/{paypal_subscription_id}",
            headers=headers,
            timeout=REQUEST_TIMEOUT_S,
        )
        response.raise_for_status()
    except RequestException as error:
        logger.exception("Failed to fetch PayPal subscription")
        raise PayPalError(error) from error

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
        try:
            subscription = get_subscription(
                paypal_subscription_id=paypal_subscription_id,
            )
        except PayPalError:
            return False

        status = subscription["status"]

        # Cache the status for one day
        cache.set(
            cache_key,
            status,
            ONE_DAY_S,  # 24 hours
        )

    return status == "ACTIVE"
