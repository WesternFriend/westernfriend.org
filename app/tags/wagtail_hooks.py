from wagtail.contrib.modeladmin.options import ModelAdmin, modeladmin_register
from wagtail.admin.panels import FieldPanel
from taggit.models import Tag


class TagsModelAdmin(ModelAdmin):
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


modeladmin_register(TagsModelAdmin)
