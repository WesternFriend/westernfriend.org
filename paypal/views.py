import http
import json
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from orders.models import Order

from . import paypal


def create_paypal_order(
    request,
) -> dict:
    """Create a PayPal order.

    Return the PayPal response."""

    body_json = json.loads(
        request.body.decode("utf-8"),
    )

    order = get_object_or_404(
        Order,
        id=body_json["wf_order_id"],
    )

    paypal_response = paypal.create_order(
        value_usd=str(
            order.get_total_cost(),
        ),
    )

    paypal_response.raise_for_status()

    return JsonResponse(paypal_response.json())


def capture_paypal_order(
    request,
) -> None:
    """Capture a PayPal order.

    Return the PayPal response."""

    body_json = json.loads(
        request.body.decode("utf-8"),
    )

    paypal_order_id = body_json["paypalOrderId"]

    paypal_response = paypal.capture_order(
        paypal_order_id=paypal_order_id,
    )
    # TODO: Attach paypal_payment_id to order
    paypal_response.raise_for_status()

    return JsonResponse(
        paypal_response.json(),
        status=paypal_response.status_code,
    )
