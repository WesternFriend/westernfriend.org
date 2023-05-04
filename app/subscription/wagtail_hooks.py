from wagtail.contrib.modeladmin.options import ModelAdmin, modeladmin_register

from subscription.models import Subscription


class SubscriptionModelAdmin(ModelAdmin):
    """Subscription admin."""

    model = Subscription
    menu_label = "Subscriptions"
    menu_icon = "placeholder"
    menu_order = 290
    add_to_settings_menu = False
    exclude_from_explorer = False
    list_display = (
        "subscriber_given_name",
        "subscriber_family_name",
        "user",
        "magazine_format",
        "price_group",
        "price",
        "paid",
        "recurring",
        "end_date",
    )
    search_fields = (
        "user",
        "subscriber_given_name",
        "subscriber_family_name",
    )
    list_filter = (
        "paid",
        "magazine_format",
        "price_group",
    )
    inspect_view_enabled = True
    inspect_view_fields = [
        "subscriber_full_name",
        "price",
        "paid",
        "recurring",
        "end_date",
    ]
    # inspect_template_name = "store/inspect_order.html"


modeladmin_register(SubscriptionModelAdmin)
