from django.conf import settings
from django.utils.html import format_html_join
from django.utils.safestring import SafeString
from wagtail.contrib.modeladmin.options import (
    ModelAdmin,
    ModelAdminGroup,
    modeladmin_register,
)
from wagtail import hooks

from community.models import CommunityDirectory, OnlineWorship
from contact.models import Meeting, Organization, Person
from documents.models import MeetingDocument, PublicBoardDocument
from events.models import Event
from memorials.models import Memorial
from wf_pages.models import MollyWingateBlogPage


class PersonModelAdmin(ModelAdmin):
    model = Person
    menu_icon = "user"
    menu_label = "People"
    list_per_page = 10
    ordering = ["family_name", "given_name"]
    list_display = ("family_name", "given_name")
    empty_value_display = "-"
    search_fields = ("given_name", "family_name")

    # TODO: determine why the following code does not work
    # The goal is to load the js file in the admin
    # only when the Person model is being edited
    # rather than globally as we do at the end of this file
    # form_view_extra_js = [
    #     "js/contact/person_url_slug.js",
    # ]


class MeetingModelAdmin(ModelAdmin):
    model = Meeting
    menu_icon = "home"
    menu_label = "Meetings"
    list_per_page = 10
    ordering = ["title"]
    list_display = ("title", "meeting_type")
    empty_value_display = "-"
    search_fields = ("title",)
    list_filter = ("meeting_type",)


class OrganizationModelAdmin(ModelAdmin):
    model = Organization
    menu_icon = "group"
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
    menu_icon = "user"
    menu_order = 295
    add_to_settings_menu = False
    exclude_from_explorer = False
    list_display = (
        "full_name",
        "memorial_meeting",
    )
    list_filter = ("memorial_meeting",)
    search_fields = (
        "memorial_person__family_name",
        "memorial_person__given_name",
        "memorial_meeting__title",
    )


class MollyWingateBlogPageModelAdmin(ModelAdmin):
    model = MollyWingateBlogPage
    menu_icon = "doc-full"
    menu_label = "Molly Wingate Blog"
    list_per_page = 10
    ordering = [
        "title",
    ]
    list_display = (
        "title",
        "publication_date",
    )
    empty_value_display = "-"
    search_fields = ("title",)
    list_filter = (
        "publication_date",
        "live",
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
        "-start_date",
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
    menu_icon = "globe"
    menu_label = "Online Worship"
    list_per_page = 10
    ordering = [
        "title",
    ]
    list_display = ("title",)
    empty_value_display = "-"
    search_fields = ("title",)


class PublicBoardDocumentModelAdmin(ModelAdmin):
    model = PublicBoardDocument
    menu_icon = "doc-full"
    menu_label = "Public Board Documents"
    list_per_page = 10
    ordering = [
        "title",
    ]
    list_display = ("title",)
    empty_value_display = "-"
    search_fields = ("title",)


class MeetingDocumentModelAdmin(ModelAdmin):
    model = MeetingDocument
    menu_icon = "doc-full"
    menu_label = "Meeting Documents"
    list_per_page = 10
    ordering = [
        "title",
    ]
    list_display = (
        "title",
        "publication_date",
        "publishing_meeting",
        "document_type",
    )
    empty_value_display = "-"
    search_fields = ("title",)
    list_filter = (
        "publication_date",
        "document_type",
        "live",
    )


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
        PublicBoardDocumentModelAdmin,
        MeetingDocumentModelAdmin,
        MollyWingateBlogPageModelAdmin,
    )


modeladmin_register(CommunityGroup)


@hooks.register("insert_editor_js")  # type: ignore
def editor_js() -> SafeString:
    js_files = [
        "js/contact/person_url_slug.js",
    ]
    js_includes = format_html_join(
        "\n",
        '<script src="{0}{1}"></script>',
        ((settings.STATIC_URL, filename) for filename in js_files),
    )
    return js_includes
