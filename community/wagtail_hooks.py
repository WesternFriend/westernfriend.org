from django.conf import settings
from django.utils.html import format_html_join
from django.utils.safestring import SafeString
from wagtail_modeladmin.options import (
    ModelAdmin,
    ModelAdminGroup,
    modeladmin_register,
)
from wagtail import hooks

from community.models import CommunityDirectory, OnlineWorship
from documents.models import MeetingDocument, PublicBoardDocument
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
