import json
import os

from django.http import HttpResponse
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

        return HttpResponse()