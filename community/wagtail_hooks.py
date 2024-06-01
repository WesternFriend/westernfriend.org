from django.conf import settings
from django.utils.html import format_html_join
from django.utils.safestring import SafeString
from wagtail_modeladmin.options import (
    ModelAdmin,
    ModelAdminGroup,
    modeladmin_register,
)
from wagtail import hooks

from accounts.models import User
from community.models import CommunityDirectory, OnlineWorship
from documents.models import MeetingDocument, PublicBoardDocument
from events.models import Event
from wf_pages.models import MollyWingateBlogPage


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
    search_fields = ("title",)
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


class UserModelAdmin(ModelAdmin):
    """User model admin."""

    model = User
    menu_icon = "group"
    menu_label = "Registered Users"
    list_per_page = 10
    form_fields_exclude = [
        "password",
        "user_permissions",
    ]

    ordering = [
        "last_name",
        "first_name",
    ]
    list_display = (
        "last_name",
        "first_name",
        "email",
        "date_joined",
        "is_active",
        "is_subscriber",
    )
    empty_value_display = "-"
    search_fields = (
        "first_name",
        "last_name",
        "email",
    )
    list_filter = ("is_active",)


class CommunityGroup(ModelAdminGroup):
    menu_label = "Community"
    menu_icon = "snippet"
    menu_order = 200
    items = (
        UserModelAdmin,
        EventModelAdmin,
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
