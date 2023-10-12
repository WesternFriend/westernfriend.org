import json
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST

from orders.models import Order
from subscription.models import Subscription

from . import paypal


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

    paypal_response = paypal.create_order(
        value_usd=str(
            order.get_total_cost(),
        ),
    )

    paypal_response.raise_for_status()

    return JsonResponse(paypal_response.json())


def capture_paypal_order(
    request,
) -> JsonResponse:
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


@login_required
@require_POST
def link_paypal_subscription(request) -> JsonResponse:
    """Link a PayPal subscription to a WesternFriendSubscription."""

    body_json = json.loads(
        request.body.decode("utf-8"),
    )

    subscription, created = Subscription.objects.get_or_create(
        paypal_subscription_id=body_json["subscriptionID"],
        user=request.user,
    )

    if not created:
        return JsonResponse(
            {
                "success": False,
                "error": "Subscription already exists",
            },
            status=400,
        )

    # If the subscription was created, 
    # set the user to the current user
    # as well as the PayPal Subscription ID
    subscription.user = request.user

    subscription.save()

    # Ensure the subscription is active
    # Note: there may be some delay in PayPal marking subscriptions as ACTIVE
    # that could cause this to fail even though the payment was completed.
    paypal_subscription_is_active = paypal.subscription_is_active(
        paypal_subscription_id=subscription.paypal_subscription_id,
    )
    if not paypal_subscription_is_active:
        return JsonResponse(
            {
                "success": False,
                "error": "Subscription is not active",
            },
            status=400,
        )

    return JsonResponse(
        {
            "success": True,
        },
    )