from wagtail.contrib.modeladmin.options import (
    ModelAdmin,
    ModelAdminGroup,
    modeladmin_register,
)

from .models import NewsItem


class NewsItemModelAdmin(ModelAdmin):
    model = NewsItem
    menu_icon = "list-ul"
    menu_label = "Items"
    menu_order = 100
    add_to_settings_menu = False
    exclude_from_explorer = False
    list_per_page = 10
    list_display = (
        "title",
        "publication_date",
    )
    search_fields = ("title",)
    list_filter = ("publication_date",)


class NewsAdminGroup(ModelAdminGroup):
    menu_label = "News"
    menu_icon = "comment"
    menu_order = 300
    items = (NewsItemModelAdmin,)


modeladmin_register(NewsAdminGroup)
