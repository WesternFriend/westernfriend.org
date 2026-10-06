import json
import logging
from collections.abc import Callable
from decimal import Decimal, InvalidOperation
from http import HTTPStatus

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from orders.models import Order
from subscription.models import Subscription

from .constants import DEFAULT_CURRENCY_CODE
from .orders import capture_order, create_order

logger = logging.getLogger(__name__)

_MAX_ORDER_ID = 2**63 - 1
_MAX_ORDER_ID_DIGITS = len(str(_MAX_ORDER_ID))
_MAX_PAYPAL_ID_LENGTH = 255


def _is_valid_order_id(value: object) -> bool:
    if isinstance(value, int):
        return not isinstance(value, bool) and 0 < value <= _MAX_ORDER_ID
    if not isinstance(value, str) or not value.isascii() or not value.isdecimal():
        return False

    normalized_value = value.lstrip("0")
    return bool(normalized_value) and (
        len(normalized_value) < _MAX_ORDER_ID_DIGITS
        or (
            len(normalized_value) == _MAX_ORDER_ID_DIGITS
            and normalized_value <= str(_MAX_ORDER_ID)
        )
    )


def _is_valid_paypal_id(value: object) -> bool:
    return (
        isinstance(value, str)
        and bool(value.strip())
        and len(value) <= _MAX_PAYPAL_ID_LENGTH
    )


def _parse_json_request(
    request,
    required_fields: dict[str, Callable[[object], bool]],
) -> dict | JsonResponse:
    try:
        body_json = json.loads(request.body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        body_json = None

    if not isinstance(body_json, dict) or any(
        field not in body_json or not validator(body_json[field])
        for field, validator in required_fields.items()
    ):
        return JsonResponse(
            {"error": "Invalid request body."},
            status=HTTPStatus.BAD_REQUEST,
        )

    return body_json


@require_POST
def create_paypal_order(
    request,
) -> JsonResponse:
    """Create a PayPal order.

    Return the PayPal response.
    """
    body_json = _parse_json_request(
        request,
        {"wf_order_id": _is_valid_order_id},
    )
    if isinstance(body_json, JsonResponse):
        return body_json

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
    except Exception:
        logger.exception("Error creating PayPal order")
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
    body_json = _parse_json_request(
        request,
        {"paypal_order_id": _is_valid_paypal_id},
    )
    if isinstance(body_json, JsonResponse):
        return body_json

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
    except Exception:
        logger.exception("Error capturing PayPal order")
        return JsonResponse(
            {
                "error": "Error capturing PayPal order.",
            },
            status=HTTPStatus.INTERNAL_SERVER_ERROR,
        )

    capture = get_completed_capture(paypal_response)

    capture_validation_error = None
    if capture is None:
        logger.error(
            "PayPal capture for order %s did not complete (status %s).",
            order.id,  # type: ignore
            paypal_response.get("status"),
        )
        capture_validation_error = JsonResponse(
            {
                "error": "Payment was not completed.",
            },
            status=HTTPStatus.UNPROCESSABLE_ENTITY,
        )
    elif not capture_matches_order_total(capture, order):
        logger.error(
            "PayPal capture %s for order %s has amount %s, expected %s %s.",
            capture.get("id"),
            order.id,  # type: ignore
            capture.get("amount"),
            order.get_total_cost(),
            DEFAULT_CURRENCY_CODE.value,
        )
        capture_validation_error = JsonResponse(
            {
                "error": "Payment amount does not match order total.",
            },
            status=HTTPStatus.UNPROCESSABLE_ENTITY,
        )

    if capture_validation_error:
        return capture_validation_error

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
    body_json = _parse_json_request(
        request,
        {"subscription_id": _is_valid_paypal_id},
    )
    if isinstance(body_json, JsonResponse):
        return body_json

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
