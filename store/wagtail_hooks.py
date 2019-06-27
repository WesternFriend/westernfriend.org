from wagtail.contrib.modeladmin.options import (
    ModelAdmin,
    ModelAdminGroup,
    modeladmin_register
)

from store.models import Category, Product


class CategoryModelAdmin(ModelAdmin):
    model = Category
    menu_icon = "fa-clone"
    menu_label = "Categories"
    list_per_page = 10
    list_display = ("title",)


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
        CategoryModelAdmin,
        ProductModelAdmin,
    )


modeladmin_register(StoreGroup)
