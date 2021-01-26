import os
from django.shortcuts import get_object_or_404, redirect, render

import arrow
import braintree


from donations.models import Donation
from orders.models import Order
from subscription.models import Subscription


DONATION_PLAN_ID = "recurring-donation"
MAGAZINE_SUBSCRIPTION_PLAN_ID = "magazine-subscription"

def process_braintree_subscription(request, entity, nonce):
    gateway = braintree.BraintreeGateway(
        braintree.Configuration(
            braintree.Environment.Sandbox,
            merchant_id=os.environ.get("BRAINTREE_MERCHANT_ID"),
            public_key=os.environ.get("BRAINTREE_PUBLIC_KEY"),
            private_key=os.environ.get("BRAINTREE_PRIVATE_KEY"),
        )
    )

    # Check whether entity is Donation or Subscription
    if entity._meta.model_name == "subscription":
        first_name = entity.subscriber_given_name
        last_name = entity.subscriber_family_name
        plan_id = MAGAZINE_SUBSCRIPTION_PLAN_ID
    elif entity._meta.model_name == "donation":
        first_name = entity.donor_given_name
        last_name = entity.donor_family_name
        plan_id = DONATION_PLAN_ID


    customer_result = gateway.customer.create(
        {
            "first_name": first_name,
            "last_name": last_name,
            "payment_method_nonce": nonce,
        }
    )

    if customer_result.is_success:
        # TODO: add notification/logging for error in this step

        # TODO: determine how to allow users to select "yearly" or "monthly"
        # for recurring donations

        # activate a subscription instance
        subscription_properties = {
            "payment_method_token": customer_result.customer.payment_methods[
                0
            ].token,
            # TODO: figure out how to do this without hard-coding the subscription ID
            "plan_id": plan_id,
            "price": entity.get_total_cost(),
        }

        if not entity.recurring:
            # Subscription should only be charged once since it is not recurring
            subscription_properties["number_of_billing_cycles"] = 1

        # TODO: check whether subscription should recur and set value accordingly
        subscription_result = gateway.subscription.create(
            subscription_properties
        )

        if subscription_result.is_success:
            # TODO: add notification/logging for error in this step

            # mark order as paid
            entity.paid = True

            # store Braintree Subscription ID
            entity.braintree_subscription_id = (
                subscription_result.subscription.id
            )

            if entity._meta.model_name == "subscription":
                # Extend subscription end date by one year from today
                # as both one-time and recurring subscriptions
                # start with a single year interval
                today = arrow.utcnow()
                entity.end_date = today.shift(years=+1).date()

            entity.save()

            # Make sure order and payment IDs are
            # removed from session, to prevent errors
            clear_payment_session_vars(request)

            return redirect("payment:done")
    else:
        return redirect("payment:canceled")


def process_braintree_transaction(request, entity, nonce):
    # create and submit transaction
    result = braintree.Transaction.sale(
        {
            "amount": entity.get_total_cost(),
            "payment_method_nonce": nonce,
            "options": {"submit_for_settlement": True},
        }
    )

    if result.is_success:
        # mark order as paid
        entity.paid = True

        # store Braintree transaction ID
        entity.braintree_id = result.transaction.id

        entity.save()

        # Make sure order and payment IDs are
        # removed from session, to prevent errors
        clear_payment_session_vars(request)

        return redirect("payment:done")
    else:
        return redirect("payment:canceled")


def payment_process(request, previous_page):
    # TODO: consider whether to separate these code paths now
    # since we are using different payment methods for subscriptions
    # and bookstore orders
    #
    # NOTE: for now, I am leaving the code with partially duplicate lines
    # in case it seems desirable to separate out the code paths

    processing_bookstore_order = previous_page == "bookstore_order"
    processing_donation = previous_page == "donate"
    processing_subscription = previous_page == "subscribe"

    if processing_bookstore_order:
        order_id = request.session.get("order_id")

        entity = get_object_or_404(Order, id=order_id)
    elif processing_subscription:
        subscription_id = request.session.get("subscription_id")

        entity = get_object_or_404(Subscription, id=subscription_id)
    elif processing_donation:
        donation_id = request.session.get("donation_id")

        entity = get_object_or_404(Donation, id=donation_id)

    if request.method == "POST":
        # retrieve payment nonce
        nonce = request.POST.get("payment_method_nonce", None)

        if processing_bookstore_order:
            return process_braintree_transaction(request, entity, nonce)
        
        elif processing_donation:
            if entity.recurring:
                return process_braintree_subscription(request, entity, nonce)
            
            return process_braintree_transaction(request, entity, nonce)
        
        elif processing_subscription:
            return process_braintree_subscription(request, entity, nonce)
    else:
        client_token = braintree.ClientToken.generate()

        return render(
            request,
            "payment/process.html",
            {"client_token": client_token, "payment_total": entity.get_total_cost()},
        )


def payment_done(request):
    return render(request, "payment/done.html")


def payment_canceled(request):
    return render(request, "payment/canceled.html")


def clear_payment_session_vars(request):
    # Clear out session variables
    # TODO: see if there is a better way of doing this
    # without polluting the view code
    request.session["order_id"] = None
    request.session["subscription_id"] = None
