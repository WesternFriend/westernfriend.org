from wagtail.contrib.modeladmin.options import (
    ModelAdmin,
    ModelAdminGroup,
    modeladmin_register
)

from store.models import Book


class ProductModelAdmin(ModelAdmin):
    model = Book
    menu_icon = "fa-book"
    menu_label = "Books"
    list_per_page = 10
    list_display = ("title",)


class StoreGroup(ModelAdminGroup):
    menu_label = "Store"
    menu_icon = "fa-money"
    menu_order = 300
    items = (
        ProductModelAdmin,
    )


modeladmin_register(StoreGroup)
