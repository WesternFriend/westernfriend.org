from wagtail.contrib.modeladmin.options import (
    ModelAdmin,
    ModelAdminGroup,
    modeladmin_register,
)

from facets.models import Audience, Genre, Medium, TimePeriod, Topic
from library.models import LibraryItem


class AudienceModelAdmin(ModelAdmin):
    model = Audience
    menu_icon = "folder"
    menu_label = "Audiences"
    list_per_page = 10
    list_display = ("title",)
    search_fields = "title"


class GenreModelAdmin(ModelAdmin):
    model = Genre
    menu_icon = "folder"
    menu_label = "Genres"
    list_per_page = 10
    ordering = ["title"]
    list_display = ("title",)
    search_fields = ("title",)


class MediumModelAdmin(ModelAdmin):
    model = Medium
    menu_icon = "folder"
    menu_label = "Mediums"
    list_per_page = 10
    ordering = ["title"]
    list_display = ("title",)
    search_fields = "title"


class TimePeriodModelAdmin(ModelAdmin):
    model = TimePeriod
    menu_icon = "folder"
    menu_label = "Time Periods"
    list_per_page = 10
    ordering = ["title"]
    list_display = ("title",)
    search_fields = "title"


class TopicModelAdmin(ModelAdmin):
    model = Topic
    menu_icon = "folder"
    menu_label = "Topics"
    list_per_page = 10
    ordering = ["title"]
    list_display = ("title",)
    search_fields = "title"


class LibraryItemModelAdmin(ModelAdmin):
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


@modeladmin_register
class LibraryGroup(ModelAdminGroup):
    menu_label = "Library"
    menu_icon = "clipboard-list"
    menu_order = 200
    items = (
        LibraryItemModelAdmin,
        AudienceModelAdmin,
        GenreModelAdmin,
        MediumModelAdmin,
        TimePeriodModelAdmin,
        TopicModelAdmin,
    )
