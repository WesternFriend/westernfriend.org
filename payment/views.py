import logging

from django.conf import settings


from braintree.exceptions import AuthorizationError as BraintreeAuthorizationError
from braintree import SuccessfulResult
from braintree import ErrorResult
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from orders.models import Order

from payment.helpers import get_braintree_gateway


paypal_client_id = settings.PAYPAL_CLIENT_ID

MAGAZINE_SUBSCRIPTION_PLAN_ID = "magazine-subscription"

logger = logging.getLogger(__name__)

braintree_gateway = get_braintree_gateway()


def render_payment_processing_page(
    request: HttpRequest,
    order: Order,
) -> HttpResponse:
    """Render the payment processing page."""

    return render(
        request,
        "payment/process.html",
        {
            "paypal_client_id": paypal_client_id,
            "order": order,
        },
    )


def construct_subscription_properties(
    payment_method_token: str,
    plan_id: str,
    price: int,
    recurring: bool,
) -> dict[str, str | int]:
    """Construct a dictionary of properties for a Braintree subscription."""

    subscription_properties: dict[str, str | int] = {
        "payment_method_token": payment_method_token,
        "plan_id": plan_id,
        "price": price,
    }

    if not recurring:
        # Subscription should only be charged once since it is not recurring
        subscription_properties["number_of_billing_cycles"] = 1

    return subscription_properties


def process_braintree_subscription(
    first_name: str,
    last_name: str,
    plan_id: str,
    price: int,
    recurring: bool,
    nonce: str,
) -> SuccessfulResult | ErrorResult:
    """Process a subscription payment with Braintree."""

    customer_result = braintree_gateway.customer.create(
        {
            "first_name": first_name,
            "last_name": last_name,
            "payment_method_nonce": nonce,
        },
    )

    if customer_result.is_success:
        # TODO: add notification/logging for error in this step

        subscription_properties = construct_subscription_properties(
            payment_method_token=customer_result.customer.payment_methods[0].token,  # type: ignore  # noqa: E501
            plan_id=plan_id,
            price=price,
            recurring=recurring,
        )

        return braintree_gateway.subscription.create(subscription_properties)
    else:
        return customer_result


def process_braintree_transaction(
    amount: int,
    nonce: str,
) -> SuccessfulResult | ErrorResult:
    """Process a one-time payment with Braintree."""

    try:
        result = braintree_gateway.transaction.sale(
            {
                "amount": amount,
                "payment_method_nonce": nonce,
                "options": {
                    "submit_for_settlement": True,
                },
            },
        )
        return result
    except BraintreeAuthorizationError as exception:
        logger.warning(
            msg=f"Braintree transaction failed authorization: {exception}",  # noqa: E501
        )
        return exception


def process_bookstore_order_payment(
    request: HttpRequest,
    order_id: int,
) -> HttpResponse:
    """Process a payment for a bookstore order."""

    order = get_object_or_404(Order, id=order_id)

    return render_payment_processing_page(
        request=request,
        order=order,
    )


def process_subscription_payment(
    request: HttpRequest,
    subscription_id: int,
) -> HttpResponse:
    """Process a payment for a subscription."""

    from subscription.models import Subscription
    from subscription.views import calculate_end_date_from_braintree_subscription

    subscription = get_object_or_404(Subscription, id=subscription_id)

    if request.method == "POST":
        nonce = request.POST.get("payment_method_nonce", None)

        if nonce is None:
            logger.warning(
                msg="Braintree subscription payment failed: nonce is None",
            )
            return render_payment_processing_page(
                request=request,
                payment_total=subscription.get_total_cost(),
            )

        braintree_result = process_braintree_subscription(
            first_name=subscription.subscriber_given_name,
            last_name=subscription.subscriber_family_name,
            plan_id=MAGAZINE_SUBSCRIPTION_PLAN_ID,
            price=subscription.price,
            recurring=subscription.recurring,
            nonce=nonce,
        )

        if braintree_result.is_success is True:
            subscription.paid = True

            subscription.braintree_subscription_id = braintree_result.subscription.id  # type: ignore  # noqa: E501

            subscription.end_date = calculate_end_date_from_braintree_subscription(
                # Ignoring the following type warning since we assume that the
                # braintree_result.subscription value should exist
                braintree_subscription=braintree_result.subscription,  # type: ignore
                current_subscription_end_date=subscription.end_date,
            )
            subscription.save()

            return redirect("payment:done")
        else:
            logger.warning(
                msg=f"Braintree subscription failed: {braintree_result.message}",  # type: ignore  # noqa: E501
            )
            return redirect("payment:canceled")
    else:
        return render_payment_processing_page(
            request=request,
            payment_total=subscription.get_total_cost(),
        )


def payment_done(
    request: HttpRequest,
) -> HttpResponse:
    return render(request, "payment/done.html")


def payment_canceled(
    request: HttpRequest,
) -> HttpResponse:
    return render(request, "payment/canceled.html")
