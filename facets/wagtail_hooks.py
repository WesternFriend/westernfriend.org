from wagtail.contrib.modeladmin.options import (
    ModelAdmin,
    ModelAdminGroup,
    modeladmin_register
)

from wagtail.core import hooks

from facets.models import (
    Audience,
    Genre,
    Medium,
    TimePeriod,
    Topic,
)


class AudienceModelAdmin(ModelAdmin):
    model = Audience
    menu_icon = "group"
    menu_label = "Audience"
    list_per_page = 10
    list_display = ("title",)
    search_fields = ("title")


class GenreModelAdmin(ModelAdmin):
    model = Genre
    menu_icon = "fa-book"
    menu_label = "Genre"
    list_per_page = 10
    ordering = ["title"]
    list_display = ("title",)
    search_fields = ("title",)


class MediumModelAdmin(ModelAdmin):
    model = Medium
    menu_icon = "fa-paperclip"
    menu_label = "Medium"
    list_per_page = 10
    ordering = ["title"]
    list_display = ("title",)
    search_fields = ("title")


class TimePeriodModelAdmin(ModelAdmin):
    model = TimePeriod
    menu_icon = "fa-calendar"
    menu_label = "Time Period"
    list_per_page = 10
    ordering = ["title"]
    list_display = ("title",)
    search_fields = ("title")


class TopicModelAdmin(ModelAdmin):
    model = Topic
    menu_icon = "fa-commenting"
    menu_label = "Topic"
    list_per_page = 10
    ordering = ["title"]
    list_display = ("title",)
    search_fields = ("title")


class FacetsGroup(ModelAdminGroup):
    menu_label = "Facets"
    menu_icon = "fa-diamond"
    menu_order = 300
    items = (
        AudienceModelAdmin,
        GenreModelAdmin,
        MediumModelAdmin,
        TimePeriodModelAdmin,
        TopicModelAdmin,
    )


modeladmin_register(FacetsGroup)
