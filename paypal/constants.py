from django.conf import settings
from paypal.models import CurrencyCode


PAYPAL_ORDER_BASE_URL = f"{settings.PAYPAL_API_URL}/v2/checkout/orders"  # type: ignore
PAYPAL_SUBSCRIPTIONS_BASE_URL = f"{settings.PAYPAL_API_URL}/v1/billing/subscriptions"  # type: ignore

DEFAULT_CURRENCY_CODE = CurrencyCode.USD

ONE_DAY_S = 60 * 60 * 24  # 24 hours
