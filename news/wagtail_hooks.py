from wagtail.contrib.modeladmin.options import (
    ModelAdmin,
    ModelAdminGroup,
    modeladmin_register,
)

from .models import NewsItem, NewsTopic, NewsType


class NewsTopicModelAdmin(ModelAdmin):
    model = NewsTopic
    menu_icon = "tag"
    menu_label = "Topic"
    menu_order = 200
    add_to_settings_menu = False
    exclude_from_explorer = False
    list_per_page = 10
    list_display = ("title",)
    search_fields = ("title",)


class NewsTypeModelAdmin(ModelAdmin):
    model = NewsType
    menu_icon = "tag"
    menu_label = "Type"
    menu_order = 200
    add_to_settings_menu = False
    exclude_from_explorer = False
    list_per_page = 10
    list_display = ("title",)
    search_fields = ("title",)


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
    items = (
        NewsItemModelAdmin,
        NewsTopicModelAdmin,
        NewsTypeModelAdmin,
    )


modeladmin_register(NewsAdminGroup)
