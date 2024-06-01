from django.conf import settings
from django.utils.html import format_html_join
from django.utils.safestring import SafeString
from wagtail_modeladmin.options import (
    ModelAdmin,
    ModelAdminGroup,
    modeladmin_register,
)
from wagtail import hooks

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


class CommunityGroup(ModelAdminGroup):
    menu_label = "Community"
    menu_icon = "snippet"
    menu_order = 200
    items = (MollyWingateBlogPageModelAdmin,)


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
