from django.urls import path
from subscription.views import SubscriptionWebhookView

urlpatterns = [
    path("braintree-subscription-webhook/", SubscriptionWebhookView.as_view()),
]
