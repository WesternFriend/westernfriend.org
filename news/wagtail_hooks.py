from wagtail.admin.viewsets.model import ModelViewSet, ModelViewSetGroup
from wagtail import hooks

from .models import NewsItem, NewsTopic, NewsType


class NewsTopicViewSet(ModelViewSet):
    model = NewsTopic
    menu_icon = "tag"
    menu_label = "Topic"
    menu_order = 200
    add_to_settings_menu = False
    exclude_from_explorer = False
    list_per_page = 10
    list_display = ("title",)
    search_fields = ("title",)


class NewsTypeViewSet(ModelViewSet):
    model = NewsType
    menu_icon = "tag"
    menu_label = "Type"
    menu_order = 200
    add_to_settings_menu = False
    exclude_from_explorer = False
    list_per_page = 10
    list_display = ("title",)
    search_fields = ("title",)


class NewsItemViewSet(ModelViewSet):
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


class NewsAdminGroup(ModelViewSetGroup):
    menu_label = "News"
    menu_icon = "comment"
    menu_order = 300
    items = (
        NewsItemViewSet,
        NewsTopicViewSet,
        NewsTypeViewSet,
    )


news_viewset = NewsAdminGroup("news")  # defines /admin/news/ as the base URL


@hooks.register("register_news_viewset")
def register_viewset():
    return news_viewset
