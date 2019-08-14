from wagtail.contrib.modeladmin.options import (
    ModelAdmin,
    ModelAdminGroup,
    modeladmin_register
)

from store.models import Book
from orders.models import Order


class BookModelAdmin(ModelAdmin):
    model = Book
    menu_icon = "fa-book"
    menu_label = "Books"
    list_per_page = 10
    list_display = ("title",)


class OrderModelAdmin(ModelAdmin):
    """Order admin."""

    model = Order
    menu_label = "Orders"
    menu_icon = "placeholder"
    menu_order = 290
    add_to_settings_menu = False
    exclude_from_explorer = False
    list_display = ("email", "full_name", "paid",)
    search_fields = ("email", "given_name", "family_name")
    list_filter = ("paid",)


class StoreGroup(ModelAdminGroup):
    menu_label = "Store"
    menu_icon = "fa-money"
    menu_order = 300
    items = (
        BookModelAdmin,
        OrderModelAdmin,
    )


modeladmin_register(StoreGroup)
