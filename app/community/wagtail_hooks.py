from django.conf import settings
from django.utils.html import format_html_join
from wagtail.contrib.modeladmin.options import (
    ModelAdmin,
    ModelAdminGroup,
    modeladmin_register,
)
from wagtail import hooks

from community.models import CommunityDirectory, OnlineWorship
from contact.models import Meeting, Organization, Person
from events.models import Event
from memorials.models import Memorial


class PersonModelAdmin(ModelAdmin):
    model = Person
    menu_icon = "user"
    menu_label = "People"
    list_per_page = 10
    ordering = ["family_name", "given_name"]
    list_display = ("family_name", "given_name")
    empty_value_display = "-"
    search_fields = ("given_name", "family_name")


class MeetingModelAdmin(ModelAdmin):
    model = Meeting
    menu_icon = "group"
    menu_label = "Meetings"
    list_per_page = 10
    ordering = ["title"]
    list_display = ("title", "meeting_type")
    empty_value_display = "-"
    search_fields = ("title",)
    list_filter = ("meeting_type",)


class OrganizationModelAdmin(ModelAdmin):
    model = Organization
    menu_icon = "home"
    menu_label = "Organizations"
    list_per_page = 10
    ordering = ["title"]
    list_display = ("title",)
    empty_value_display = "-"
    search_fields = ("title",)


class MemorialModelAdmin(ModelAdmin):
    """Memorial model admin."""

    model = Memorial
    menu_label = "Memorials"
    menu_icon = "fa-circle-o-notch"
    menu_order = 295
    add_to_settings_menu = False
    exclude_from_explorer = False
    list_display = ("full_name", "memorial_meeting")
    search_fields = (
        "user",
        "given_name",
        "family_name",
    )


class EventModelAdmin(ModelAdmin):
    model = Event
    menu_icon = "date"
    menu_label = "Events"
    menu_order = 200
    add_to_settings_menu = False
    exclude_from_explorer = False
    list_per_page = 10
    ordering = [
        "start_date",
    ]
    list_display = (
        "title",
        "start_date",
        "end_date",
        "live",
    )
    empty_value_display = "-"
    search_fields = (
        "title",
        "description",
    )
    list_filter = (
        "start_date",
        "category",
        "live",
    )


class CommunityDirectoryModelAdmin(ModelAdmin):
    model = CommunityDirectory
    menu_icon = "group"
    menu_label = "Directories"
    list_per_page = 10
    ordering = [
        "title",
    ]
    list_display = ("title",)
    empty_value_display = "-"
    search_fields = ("title",)


class OnlineWorshipModelAdmin(ModelAdmin):
    model = OnlineWorship
    menu_icon = "fa-microphone"
    menu_label = "Online Worship"
    list_per_page = 10
    ordering = [
        "title",
    ]
    list_display = ("title",)
    empty_value_display = "-"
    search_fields = ("title",)


class CommunityGroup(ModelAdminGroup):
    menu_label = "Community"
    menu_icon = "snippet"
    menu_order = 200
    items = (
        PersonModelAdmin,
        MeetingModelAdmin,
        OrganizationModelAdmin,
        EventModelAdmin,
        MemorialModelAdmin,
        CommunityDirectoryModelAdmin,
        OnlineWorshipModelAdmin,
    )


modeladmin_register(CommunityGroup)


@hooks.register("insert_editor_js")
def editor_js():
    js_files = [
        "js/contact_person_slug.js",
    ]
    js_includes = format_html_join(
        "\n",
        '<script src="{0}{1}"></script>',
        ((settings.STATIC_URL, filename) for filename in js_files),
    )
    return js_includes
