from django.shortcuts import get_object_or_404, redirect, render

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
