from django.utils.html import format_html_join
from django.conf import settings

from wagtail.contrib.modeladmin.options import (
    ModelAdmin,
    ModelAdminGroup,
    modeladmin_register,
)

from wagtail.core import hooks

from .models import Person, Meeting, Organization


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


class ContactsGroup(ModelAdminGroup):
    menu_label = "Contacts"
    menu_icon = "mail"
    menu_order = 200
    items = (PersonModelAdmin, MeetingModelAdmin, OrganizationModelAdmin)


modeladmin_register(ContactsGroup)


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
