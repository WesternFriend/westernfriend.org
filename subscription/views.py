import json
import os
from datetime import timedelta

import braintree
from braintree import WebhookNotification
from django.http import HttpRequest, HttpResponse
from django.http.response import HttpResponseBase
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from subscription.models import Subscription

braintree_environment = (
    braintree.Environment.Production  # type: ignore
    if os.environ.get("BRAINTREE_ENVIRONMENT") == "production"
    else braintree.Environment.Sandbox  # type: ignore
)

braintree_gateway = braintree.BraintreeGateway(
    braintree.Configuration(
        braintree_environment,
        merchant_id=os.environ.get("BRAINTREE_MERCHANT_ID"),
        public_key=os.environ.get("BRAINTREE_PUBLIC_KEY"),
        private_key=os.environ.get("BRAINTREE_PRIVATE_KEY"),
    )
)


def handle_subscription_webhook(
    webhook_notification: WebhookNotification,
) -> None:
    braintree_subscription = webhook_notification.subscription

    # Make sure we can find the subscription
    subscription = get_object_or_404(
        Subscription,
        braintree_subscription_id=braintree_subscription.id,
    )

    # webhook_notification.kind should be available on the notification object
    # https://developer.paypal.com/braintree/docs/reference/general/webhooks/subscription/python
    if webhook_notification.kind == "subscription_charged_successfully":  # type: ignore
        # Grace period so subscribers maintain access
        grace_period = timedelta(days=5)

        # Use Braintree paid through date (with grace period), if available
        if braintree_subscription.get("paid_through_date"):
            subscription.end_date = (
                braintree_subscription.paid_through_date + grace_period
            )
        # Otherwise extend by one year with grace period
        else:
            one_year_with_grace: timedelta = timedelta(days=365) + grace_period

            subscription.end_date = subscription.end_date + one_year_with_grace

        subscription.save()  # type: ignore


class SubscriptionWebhookView(View):
    @method_decorator(csrf_exempt)
    def dispatch(
        self,
        request: HttpRequest,
        *args: tuple,
        **kwargs: dict,
    ) -> HttpResponseBase:
        return super().dispatch(request, *args, **kwargs)

    def post(
        self,
        request: HttpRequest,
        *args: tuple,
        **kwargs: dict,
    ) -> HttpResponse:
        # Parse Braintree webhook
        # https://developer.paypal.com/braintree/docs/guides/webhooks/parse
        body: dict = json.loads(request.body)
        webhook_notification: WebhookNotification = (
            braintree_gateway.webhook_notification.parse(
                body["bt_signature"],
                body["bt_payload"],
            )
        )

        if webhook_notification.subscription:
            handle_subscription_webhook(
                webhook_notification=webhook_notification,
            )

        return HttpResponse()
