from wagtail.contrib.modeladmin.options import ModelAdmin, modeladmin_register

from community.models import CommunityResource


class CommunityResourceModelAdmin(ModelAdmin):
    model = CommunityResource
    menu_icon = "link"
    menu_label = "Resources"
    menu_order = 300
    add_to_settings_menu = False
    exclude_from_explorer = False
    list_per_page = 10
    ordering = ["title"]
    list_display = ("title", "resource_type")
    empty_value_display = "-"
    search_fields = ("title")
    list_filter = ("resource_type",)


modeladmin_register(CommunityResourceModelAdmin)
