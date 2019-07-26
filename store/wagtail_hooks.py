from wagtail.contrib.modeladmin.options import (
    ModelAdmin,
    ModelAdminGroup,
    modeladmin_register
)

from store.models import Product


class ProductModelAdmin(ModelAdmin):
    model = Product
    menu_icon = "fa-gift"
    menu_label = "Products"
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
