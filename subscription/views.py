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

        subscription = get_object_or_404(
            Subscription,
            pk=webhook_notification.subscription.id
        )

        if webhook_notification.kind == "subscription_charged_successfully":
            one_year_with_grace = timedelta(days=370)

            subscription.end_date = subscription.end_date + one_year_with_grace
            subscription.save()
            
        return HttpResponse()