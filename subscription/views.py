from datetime import timedelta
import json
import os

from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

import braintree

from subscription.models import Subscription

class SubscriptionWebhookView(View):

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        gateway = braintree.BraintreeGateway(
            braintree.Configuration(
                braintree.Environment.Sandbox,
                merchant_id=os.environ.get("BRAINTREE_MERCHANT_ID"),
                public_key=os.environ.get("BRAINTREE_PUBLIC_KEY"),
                private_key=os.environ.get("BRAINTREE_PRIVATE_KEY")
            )
        )

        body = json.loads(request.body)

        webhook_notification = gateway.webhook_notification.parse(
            body["bt_signature"],
            body["bt_payload"]
        )

        braintree_subscription = webhook_notification.subscription

        # Make sure we can find the subscription
        subscription = get_object_or_404(
            Subscription,
            braintree_subscription_id=braintree_subscription.id
        )

        if webhook_notification.kind == "subscription_charged_successfully":
            # Grace period so subscribers maintain access
            grace_period = timedelta(days=5)

            # Use Braintree paid through date (with grace period), if available
            if braintree_subscription.get("paid_through_date"):
                subscription.end_date = braintree_subscription.paid_through_date + grace_period
            # Otherwise extend by one year with grace period
            else:
                one_year_with_grace = timedelta(days=365) + grace_period

                subscription.end_date = subscription.end_date + one_year_with_grace
            
            subscription.save()

        return HttpResponse()