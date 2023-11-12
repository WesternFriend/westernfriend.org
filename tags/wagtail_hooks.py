from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet
from wagtail.admin.panels import FieldPanel
from taggit.models import Tag


class TagsSnippetViewSet(SnippetViewSet):
    Tag.panels = [
        FieldPanel("name"),
    ]
    model = Tag
    menu_label = "Tags"
    menu_icon = "tag"
    menu_order = 200
    list_display = [
        "name",
        "slug",
    ]
    search_fields = ("name",)


register_snippet(TagsSnippetViewSet)
