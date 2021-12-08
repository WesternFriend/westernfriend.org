from wagtail.contrib.modeladmin.options import (
    ModelAdmin,
    ModelAdminGroup,
    modeladmin_register,
)

from .models import NewsTopic, NewsType

class NewsTopicModelAdmin(ModelAdmin):
    model = NewsTopic
    menu_icon = "folder-inverse"
    menu_label = "Topic"
    menu_order = 100
    add_to_settings_menu = False
    exclude_from_explorer = False
    list_per_page = 10
    list_display = ("title",)
    search_fields = ("title",)


class NewsTypeModelAdmin(ModelAdmin):
    model = NewsType
    menu_icon = "folder-inverse"
    menu_label = "Type"
    menu_order = 100
    add_to_settings_menu = False
    exclude_from_explorer = False
    list_per_page = 10
    list_display = ("title",)
    search_fields = ("title",)


class NewsAdminGroup(ModelAdminGroup):
    menu_label = "News"
    menu_icon = "fa-newspaper-o"
    menu_order = 300
    items = (
        NewsTopicModelAdmin,
        NewsTypeModelAdmin,
    )


modeladmin_register(NewsAdminGroup)
