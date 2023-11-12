from wagtail.admin.viewsets.model import ModelViewSet, ModelViewSetGroup
from wagtail import hooks

from facets.models import Audience, Genre, Medium, TimePeriod, Topic
from library.models import LibraryItem


class AudienceViewSet(ModelViewSet):
    model = Audience
    menu_icon = "tag"
    menu_label = "Audiences"
    list_per_page = 10
    list_display = ("title",)
    search_fields = "title"


class GenreViewSet(ModelViewSet):
    model = Genre
    menu_icon = "tag"
    menu_label = "Genres"
    list_per_page = 10
    ordering = ["title"]
    list_display = ("title",)
    search_fields = ("title",)


class MediumViewSet(ModelViewSet):
    model = Medium
    menu_icon = "tag"
    menu_label = "Mediums"
    list_per_page = 10
    ordering = ["title"]
    list_display = ("title",)
    search_fields = "title"


class TimePeriodViewSet(ModelViewSet):
    model = TimePeriod
    menu_icon = "tag"
    menu_label = "Time Periods"
    list_per_page = 10
    ordering = ["title"]
    list_display = ("title",)
    search_fields = "title"


class TopicViewSet(ModelViewSet):
    model = Topic
    menu_icon = "tag"
    menu_label = "Topics"
    list_per_page = 10
    ordering = ["title"]
    list_display = ("title",)
    search_fields = "title"


class LibraryItemViewSet(ModelViewSet):
    model = LibraryItem
    menu_icon = "list-ul"
    menu_label = "Items"
    menu_order = 110
    list_per_page = 10
    list_display = (
        "title",
        "item_audience",
        "item_genre",
        "item_medium",
        "item_time_period",
    )
    list_filter = (
        "item_audience",
        "item_genre",
        "item_medium",
        "item_time_period",
    )
    search_fields = ("title",)


class LibraryGroup(ModelViewSetGroup):
    menu_label = "Library"
    menu_icon = "clipboard-list"
    menu_order = 200
    items = (
        LibraryItemViewSet,
        AudienceViewSet,
        GenreViewSet,
        MediumViewSet,
        TimePeriodViewSet,
        TopicViewSet,
    )


hooks.register("register_library_viewset", LibraryGroup)
