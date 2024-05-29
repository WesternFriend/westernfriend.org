from http import HTTPStatus
import json
import logging
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from orders.models import Order
from subscription.models import Subscription

from .orders import capture_order, create_order

logger = logging.getLogger(__name__)


@require_POST
def create_paypal_order(
    request,
) -> JsonResponse:
    """Create a PayPal order.

    Return the PayPal response.
    """

    body_json = json.loads(
        request.body.decode("utf-8"),
    )

    try:
        order = Order.objects.get(
            id=body_json["wf_order_id"],
        )
    except Order.DoesNotExist:
        logger.exception(
            "Order with ID %s does not exist.",
            body_json["wf_order_id"],
        )
        return JsonResponse(
            {
                "error": "Order does not exist.",
            },
            status=HTTPStatus.NOT_FOUND,
        )

    try:
        paypal_response = create_order(
            value_usd=str(
                order.get_total_cost(),
            ),
        )
        logger.info(
            "PayPal order created: %s",
            paypal_response,
        )
    except Exception as exception:
        logger.exception(exception)
        return JsonResponse(
            {
                "error": "Error creating PayPal order.",
            },
            status=HTTPStatus.INTERNAL_SERVER_ERROR,
        )

    paypal_order_id: str = paypal_response.get("id", "")

    order.paypal_order_id = paypal_order_id
    order.save()

    return JsonResponse(
        data={
            "paypal_order_id": paypal_order_id,
        },
        status=HTTPStatus.CREATED,
    )


@require_POST
def capture_paypal_order(
    request,
) -> JsonResponse:
    """Capture a PayPal order.

    Return the PayPal response.
    """

    body_json = json.loads(request.body.decode("utf-8"))

    paypal_order_id = body_json["paypal_order_id"]
    paypal_payment_id = body_json["paypal_payment_id"]

    # First, verify the order exists in our database
    try:
        order = Order.objects.get(
            paypal_order_id=paypal_order_id,  # type: ignore
        )
    except Order.DoesNotExist:
        logger.exception(
            "Order with PayPal order ID %s does not exist.",
            paypal_order_id,  # type: ignore
        )
        return JsonResponse(
            {
                "error": "Order does not exist.",
            },
            status=404,
        )

    # Then, capture the order payment in PayPal
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
    # Get transaction ID from PayPal response
    # paypal_response.purchase_units[0].payments.captures[0].id
    # but make sure to get it safely since there may be null or undefined values
    transaction_id = (
        paypal_response.get("purchase_units", [{}])[0]
        .get("payments", {})
        .get("captures", [{}])[0]
        .get("id", "")
    )

    # Finally, update the order in our database
    # with the PayPal payment ID and mark it as paid
    order.paypal_payment_id = paypal_payment_id
    order.paypal_transaction_id = transaction_id
    order.paid = True
    order.save()

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

    subscription, _ = Subscription.objects.get_or_create(
        user=request.user,
    )
    subscription.paypal_subscription_id = body_json["subscription_id"]
    subscription.save()

    return JsonResponse(
        {
            "success": True,
        },
    )
