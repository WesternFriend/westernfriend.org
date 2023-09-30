import logging

import braintree
from braintree.exceptions import AuthorizationError as BraintreeAuthorizationError
from braintree import SuccessfulResult
from braintree import ErrorResult
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from donations.models import Donation
from orders.models import Order
from payment.helpers import get_braintree_gateway


RECURRING_DONATION_PLAN_IDS = {
    "monthly": "monthly-recurring-donation",
    "yearly": "yearly-recurring-donation",
}

MAGAZINE_SUBSCRIPTION_PLAN_ID = "magazine-subscription"

logger = logging.getLogger(__name__)

braintree_gateway = get_braintree_gateway()

def render_payment_processing_page(
    request: HttpRequest,
    payment_total: int,
) -> HttpResponse:
    client_token = braintree.ClientToken.generate()

    return render(
        request,
        "payment/process.html",
        {
            "client_token": client_token,
            "payment_total": payment_total,
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


def process_braintree_recurring_donation(
    donation: Donation,
    nonce: str,
) -> HttpResponse:
    """Process a recurring donation payment as a Braintree subscription."""

    braintree_result = process_braintree_subscription(
        first_name=donation.donor_given_name,
        last_name=donation.donor_family_name,
        # Ignoring the following type warning since we know that the
        # donation.recurrence value is a valid key in the
        # RECURRING_DONATION_PLAN_IDS dictionary
        plan_id=RECURRING_DONATION_PLAN_IDS[donation.recurrence],  # type: ignore
        price=donation.get_total_cost(),
        recurring=donation.recurring,
        nonce=nonce,
    )

    if braintree_result is not None and braintree_result.is_success:
        donation.paid = True

        # ignoring the following type warning since we know that the
        # braintree_result.subscription.id value should exist
        donation.braintree_subscription_id = braintree_result.subscription.id  # type: ignore  # noqa: E501

        donation.save()

        return redirect("payment:done")

    return redirect("payment:canceled")


def process_braintree_single_donation(
    donation: Donation,
    nonce: str,
) -> HttpResponse:
    """Process a one-time donation payment as a Braintree transaction."""

    braintree_result = process_braintree_transaction(
        amount=donation.get_total_cost(),
        nonce=nonce,
    )

    if braintree_result.is_success:
        donation.paid = True

        donation.braintree_transaction_id = braintree_result.transaction.id  # type: ignore  # noqa: E501

        donation.save()

        return redirect("payment:done")

    return redirect("payment:canceled")


def process_donation_payment(
    request: HttpRequest,
    donation_id: int,
) -> HttpResponse:
    """Process a payment for a donation."""

    donation = get_object_or_404(Donation, id=donation_id)

    if request.method == "POST":
        nonce = request.POST.get("payment_method_nonce", None)

        if nonce is None:
            logger.warning(
                msg="Braintree donation payment failed: nonce is None",
            )
            return render_payment_processing_page(
                request=request,
                payment_total=donation.get_total_cost(),
            )

        if donation.recurring is True:
            return process_braintree_recurring_donation(donation, nonce)

        return process_braintree_single_donation(donation, nonce)
    else:
        return render_payment_processing_page(
            request=request,
            payment_total=donation.get_total_cost(),
        )


def process_bookstore_order_payment(
    request: HttpRequest,
    order_id: int,
) -> HttpResponse:
    """Process a payment for a bookstore order."""

    order = get_object_or_404(Order, id=order_id)
    if request.method == "POST":
        nonce = request.POST.get("payment_method_nonce", None)

        if nonce is None:
            logger.warning(
                msg="Braintree order payment failed: nonce is None",
            )
            return render_payment_processing_page(
                request=request,
                payment_total=order.get_total_cost(),
            )

        braintree_result = process_braintree_transaction(
            amount=order.get_total_cost(),
            nonce=nonce,
        )

        if braintree_result.is_success is True:
            order.paid = True

            order.braintree_transaction_id = braintree_result.transaction.id  # type: ignore  # noqa: E501

            order.save()

            return redirect("payment:done")

        return redirect("payment:canceled")
    else:
        return render_payment_processing_page(
            request=request,
            payment_total=order.get_total_cost(),
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
