from wagtail.admin.viewsets.model import ModelViewSet
from wagtail import hooks

from subscription.models import Subscription


class SubscriptionViewSet(ModelViewSet):
    """Subscription admin."""

    model = Subscription
    menu_label = "Subscriptions"
    menu_icon = "placeholder"
    menu_order = 290
    add_to_settings_menu = False
    exclude_from_explorer = False
    list_display = (
        "user",
        "paypal_subscription_id",
        "expiration_date",
        # TODO: consider and test the performance impact
        # of including is_active in the list display.
        # "is_active",
    )
    search_fields = (
        "user",
        "paypal_subscription_id",
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
    # inspect_template_name = "store/inspect_order.html"


subscription_viewset = SubscriptionViewSet("subscription")  # defines /admin/subscription/ as the base URL

@hooks.register("register_subscription_viewset")
def register_viewset():
    return subscription_viewset
