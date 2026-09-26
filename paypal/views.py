from decimal import Decimal, InvalidOperation
from http import HTTPStatus
import json
import logging
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from orders.models import Order
from subscription.models import Subscription

from .constants import DEFAULT_CURRENCY_CODE
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


def get_completed_capture(paypal_response: dict) -> dict | None:
    """Return the capture from a PayPal capture response if it completed."""
    if paypal_response.get("status") != "COMPLETED":
        return None

    try:
        capture = paypal_response["purchase_units"][0]["payments"]["captures"][0]
    except (IndexError, KeyError, TypeError):
        return None

    if capture.get("status") != "COMPLETED":
        return None

    return capture


def capture_matches_order_total(capture: dict, order: Order) -> bool:
    amount = capture.get("amount") or {}

    if amount.get("currency_code") != DEFAULT_CURRENCY_CODE.value:
        return False

    try:
        captured_value = Decimal(str(amount.get("value")))
    except InvalidOperation:
        return False

    return captured_value == order.get_total_cost()


@require_POST
def capture_paypal_order(
    request,
) -> JsonResponse:
    """Capture a PayPal order and mark the matching order as paid.

    The order is only marked paid when PayPal reports a completed capture
    for the full order total.
    """

    body_json = json.loads(request.body.decode("utf-8"))

    paypal_order_id = body_json["paypal_order_id"]

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
            status=HTTPStatus.NOT_FOUND,
        )

    if order.paid:
        return JsonResponse(
            {
                "status": "COMPLETED",
            },
            status=HTTPStatus.OK,
        )

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
            status=HTTPStatus.INTERNAL_SERVER_ERROR,
        )

    capture = get_completed_capture(paypal_response)

    if capture is None:
        logger.error(
            "PayPal capture for order %s did not complete (status %s).",
            order.id,  # type: ignore
            paypal_response.get("status"),
        )
        return JsonResponse(
            {
                "error": "Payment was not completed.",
            },
            status=HTTPStatus.UNPROCESSABLE_ENTITY,
        )

    if not capture_matches_order_total(capture, order):
        logger.error(
            "PayPal capture %s for order %s has amount %s, expected %s %s.",
            capture.get("id"),
            order.id,  # type: ignore
            capture.get("amount"),
            order.get_total_cost(),
            DEFAULT_CURRENCY_CODE.value,
        )
        return JsonResponse(
            {
                "error": "Payment amount does not match order total.",
            },
            status=HTTPStatus.UNPROCESSABLE_ENTITY,
        )

    order.paypal_transaction_id = capture.get("id", "")
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
