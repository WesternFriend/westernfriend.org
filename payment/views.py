import os
from django.shortcuts import get_object_or_404, redirect, render

import arrow
import braintree

from orders.models import Order
from subscription.models import Subscription


def payment_process(request, previous_page):
    if previous_page == "bookstore_order":
        order_id = request.session.get("order_id")

        entity = get_object_or_404(Order, id=order_id)
    elif previous_page == "subscribe":
        subscription_id = request.session.get("subscription_id")

        entity = get_object_or_404(Subscription, id=subscription_id)

    if request.method == "POST":
        # retrieve payment nonce
        nonce = request.POST.get("payment_method_nonce", None)

        gateway = braintree.BraintreeGateway(
            braintree.Configuration(
                braintree.Environment.Sandbox,
                merchant_id=os.environ.get("BRAINTREE_MERCHANT_ID"),
                public_key=os.environ.get("BRAINTREE_PUBLIC_KEY"),
                private_key=os.environ.get("BRAINTREE_PRIVATE_KEY")
            )
        )

        customer_result = gateway.customer.create({
            "first_name": entity.subscriber_given_name,
            "last_name": entity.subscriber_family_name,
            "payment_method_nonce": nonce
        })

        if customer_result.is_success:
            # TODO: add notification/logging for error in this step

            # activate a subscription instance instead of transaction
            # TODO: check whether subscription should recur and set value accordingly
            subscription_result = gateway.subscription.create(
                {
                    "payment_method_token": customer_result.customer.payment_methods[0].token,
                    # TODO: figure out how to do this without hard-coding the subscription ID
                    "plan_id": "magazine-subscription",
                    "price": entity.get_total_cost(),
                }
            )

            if subscription_result.is_success:
                # TODO: add notification/logging for error in this step

                # mark order as paid
                # TODO: deprecate/remove this "paid" property
                entity.paid = True

                # store Braintree Subscription ID
                # TODO: rename this property to "braintree_subscription_id"
                entity.braintree_id = subscription_result.subscription.id

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
    else:
        client_token = braintree.ClientToken.generate()

        return render(
            request,
            "payment/process.html",
            {
                "client_token": client_token,
                "payment_total": entity.get_total_cost()
            },
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
