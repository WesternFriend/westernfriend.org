from dataclasses import dataclass
from http import HTTPStatus
import json
import logging
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST

from orders.models import Order
from subscription.models import Subscription

from .orders import capture_order, create_order

logger = logging.getLogger(__name__)


@dataclass
class CreatePayPalOrderResponse:
    order_id: str


@require_POST
def create_paypal_order(
    request,
) -> JsonResponse:
    """Create a PayPal order.

    Return the PayPal response."""

    body_json = json.loads(
        request.body.decode("utf-8"),
    )

    order = get_object_or_404(
        Order,
        id=body_json["wf_order_id"],
    )

    try:
        paypal_response = create_order(
            value_usd=str(
                order.get_total_cost(),
            ),
        )

        create_paypal_order_response = CreatePayPalOrderResponse(
            order_id=paypal_response.get('id', ''),
        )

        return JsonResponse(
            create_paypal_order_response.__dict__,
            status=HTTPStatus.CREATED,
        )
    except Exception as exception:
        logger.exception(exception)
        return JsonResponse(
            {
                "error": "Error creating PayPal order.",
            },
            status=500,
        )


def capture_paypal_order(
    request,
) -> JsonResponse:
    """Capture a PayPal order.

    Return the PayPal response."""

    body_json = json.loads(
        request.body.decode("utf-8"),
    )

    paypal_order_id = body_json["paypalOrderId"]

    try:
        paypal_response = capture_order(
            paypal_order_id=paypal_order_id,
        )
    except Exception as exception:
        logger.exception(exception)
        return JsonResponse(
            {
                "error": "Error capturing PayPal order.",
            },
            status=500,
        )

    return JsonResponse(
        paypal_response,
        status=HTTPStatus.CREATED,
    )


@login_required
@require_POST
def link_paypal_subscription(request) -> JsonResponse:
    """Link a PayPal subscription to a WesternFriendSubscription."""

    body_json = json.loads(
        request.body.decode("utf-8"),
    )

    subscription, created = Subscription.objects.get_or_create(
        user=request.user,
    )
    subscription.paypal_subscription_id = body_json["subscriptionID"]
    subscription.save()

    return JsonResponse(
        {
            "success": True,
        },
    )
