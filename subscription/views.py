from datetime import date
import json
import os
from datetime import timedelta

import braintree
from braintree import Subscription as BraintreeSubscription
from braintree import WebhookNotification
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from subscription.models import Subscription

# Grace period so subscribers maintain access
GRACE_PERIOD_DAYS = timedelta(days=5)
ONE_YEAR_WITH_GRACE_PERIOD: timedelta = timedelta(days=365) + GRACE_PERIOD_DAYS

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
    ),
)


def calculate_end_date_from_braintree_subscription(
    braintree_subscription: BraintreeSubscription,
    current_subscription_end_date: date,
) -> date:
    # Use Braintree paid through date (with grace period), if available
    if (
        hasattr(braintree_subscription, "paid_through_date")
        and braintree_subscription.paid_through_date is not None  # type: ignore
    ):
        return braintree_subscription.paid_through_date + GRACE_PERIOD_DAYS  # type: ignore  # noqa: E501
    # Otherwise extend by one year with grace period
    else:
        return current_subscription_end_date + ONE_YEAR_WITH_GRACE_PERIOD


def handle_subscription_webhook(
    braintree_subscription: BraintreeSubscription,
) -> None:
    # Make sure we can find the subscription
    subscription = get_object_or_404(
        Subscription,
        # TODO: determine why mypy cannot find the `braintree_subscription.id` property
        braintree_subscription_id=braintree_subscription.id,  # type: ignore
    )

    subscription.end_date = calculate_end_date_from_braintree_subscription(
        braintree_subscription=braintree_subscription,
        current_subscription_end_date=subscription.end_date,
    )

    subscription.save()  # type: ignore


class SubscriptionWebhookView(View):
    @method_decorator(csrf_exempt)
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
