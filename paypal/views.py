import json
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST

from orders.models import Order
from subscription.models import Subscription

from .orders import capture_order, create_order


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

    paypal_response = create_order(
        value_usd=str(
            order.get_total_cost(),
        ),
    )

    paypal_response.raise_for_status()  # type: ignore

    return JsonResponse(paypal_response.json())  # type: ignore


def capture_paypal_order(
    request,
) -> JsonResponse:
    """Capture a PayPal order.

    Return the PayPal response."""

    body_json = json.loads(
        request.body.decode("utf-8"),
    )

    paypal_order_id = body_json["paypalOrderId"]

    paypal_response = capture_order(
        paypal_order_id=paypal_order_id,
    )
    # TODO: Attach paypal_payment_id to order
    paypal_response.raise_for_status()  # type: ignore

    return JsonResponse(
        paypal_response.json(),  # type: ignore
        status=paypal_response.status_code,  # type: ignore
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
