from wagtail.contrib.modeladmin.options import (
    ModelAdmin,
    ModelAdminGroup,
    modeladmin_register,
)

from orders.models import Order
from store.models import Book


class BookModelAdmin(ModelAdmin):
    model = Book
    menu_icon = "openquote"
    menu_label = "Books"
    list_per_page = 10
    list_display = ("title",)


class OrderModelAdmin(ModelAdmin):
    """Order admin."""

    model = Order
    menu_label = "Orders"
    menu_icon = "tasks"
    menu_order = 290
    add_to_settings_menu = False
    exclude_from_explorer = False
    list_display = (
        "purchaser_email",
        "purchaser_full_name",
        "paid",
        "paypal_order_id",
        "paypal_payment_id",
    )
    search_fields = (
        "purchaser_email",
        "purchaser_given_name",
        "purchaser_family_name",
        "purchaser_meeting_or_organization",
        "recipient_name",
    )
    list_filter = ("paid",)
    inspect_view_enabled = True
    inspect_view_fields = [
        "id",
        "paid",
        "purchaser_given_name",
        "purchaser_family_name",
        "purchaser_meeting_or_organization",
        "recipient_name",
        "items",
    ]
    inspect_template_name = "store/inspect_order.html"


class StoreGroup(ModelAdminGroup):
    menu_label = "Store"
    menu_icon = "site"
    menu_order = 300
    items = (
        BookModelAdmin,
        OrderModelAdmin,
    )


modeladmin_register(StoreGroup)
