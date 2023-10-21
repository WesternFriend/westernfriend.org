from django.core.cache import cache
import requests

from paypal.constants import ONE_DAY_S, PAYPAL_SUBSCRIPTIONS_BASE_URL, construct_paypal_auth_headers

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