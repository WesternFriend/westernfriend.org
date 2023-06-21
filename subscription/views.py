from datetime import datetime
import json
import os
from datetime import timedelta

import braintree
from braintree import Subscription as BraintreeSubscription
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
    braintree_subscription: BraintreeSubscription,
) -> None:
    # Make sure we can find the subscription
    subscription = get_object_or_404(
        Subscription,
        # TODO: determine why mypy cannot find the `braintree_subscription.id` property
        braintree_subscription_id=braintree_subscription.id,  # type: ignore
    )

    # Grace period so subscribers maintain access
    grace_period = timedelta(days=5)

    # Use Braintree paid through date (with grace period), if available
    # TODO: determine why mypy can't find the `paid_through_date` property
    if (
        hasattr(braintree_subscription, "paid_through_date")
        and braintree_subscription.paid_through_date is not None
    ):  # type: ignore
        # create new paid_through_date
        # by parsing braintree_subscription.paid_through_date
        # to a datetime object
        paid_through_date = datetime.strptime(
            braintree_subscription.paid_through_date,  # type: ignore
            "%Y-%m-%d",
        ).date()

        subscription.end_date = paid_through_date + grace_period  # type: ignore
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

        # webhook_notification.kind should be available on the notification object
        # https://developer.paypal.com/braintree/docs/reference/general/webhooks/subscription/python  # noqa: E501
        if webhook_notification.kind == "subscription_charged_successfully":  # type: ignore # noqa: E501
            handle_subscription_webhook(
                braintree_subscription=webhook_notification.subscription,
            )

        return HttpResponse()
