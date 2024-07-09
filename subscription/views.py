from wagtail.admin.viewsets.model import ModelViewSet

from .models import Subscription


class SubscriptionViewSet(ModelViewSet):
    model = Subscription
    menu_label = "Subscriptions"
    icon = "placeholder"
    name = "subscriptions"
    list_display = (
        "user",
        "paypal_subscription_id",
        "expiration_date",
        "is_active",
    )
    inspect_view_enabled = True
    inspect_view_fields = [
        "user",
        "paypal_subscription_id",
        # The 'is_active' field requires an HTTP request or cache hit
        # because it fetches the current status from PayPal.
        # Adding it to the inspect view to avoid unnecessary requests.
        "is_active",
    ]
    search_fields = [
        "user__email",
        "paypal_subscription_id",
    ]
    ordering = ["user__email"]
    export_filename = "western_friend_subscriptions"
    list_export = [
        "user",
        "paypal_subscription_id",
        "expiration_date",
        "is_active",
    ]
