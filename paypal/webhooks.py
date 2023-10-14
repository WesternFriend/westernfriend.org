import json


from django.http import HttpRequest, HttpResponse
from django.http.response import HttpResponseBase
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from subscription.models import Subscription



def handle_subscription_webhook(
    webhook_payload: dict,
) -> None:
    """Handle a subscription webhook."""

    paypal_subscription_id = webhook_payload["resource"]["id"]
    # Make sure we can find the subscription
    subscription = get_object_or_404(
        Subscription,
        # TODO: determine why mypy cannot find the `braintree_subscription.id` property
        paypal_subscription_id=paypal_subscription_id,  # type: ignore
    )
    # Update the subscription status
    # Note: this is_active will need to be converted from a property
    # to a field.
    #subscription.is_active = webhook_payload["resource"]["status"] == "ACTIVE"

    subscription.save()  # type: ignore

# TODO: move this to the PayPal library
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
        # Parse PayPal webhook
        # https://developer.paypal.com/docs/subscriptions/webhooks/
        body: dict = json.loads(request.body)
        print(body)
        # Parse webhook
        # Check kind
        # update subsription status
        # handle_subscription_webhook(
        #     webhook_payload=body,
        # )

        return HttpResponse()
