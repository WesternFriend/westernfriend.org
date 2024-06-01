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
    )
    inspect_view_enabled = True
    inspect_view_fields = [
        "user",
        "paypal_subscription_id",
        # This requires an HTTP request or cache hit
        # so adding it to the inspect view
        # to, hypothetically, avoid unnecessary requests.
        "is_active",
    ]
    search_fields = [
        "user__email",
        "paypal_subscription_id",
    ]
    ordering = ["user__email"]
