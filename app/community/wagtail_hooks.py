from wagtail.contrib.modeladmin.options import (
    ModelAdmin,
    ModelAdminGroup,
    modeladmin_register,
)

from community.models import CommunityDirectory, OnlineWorship


class CommunityDirectoryModelAdmin(ModelAdmin):
    model = CommunityDirectory
    menu_icon = "group"
    menu_label = "Community Directories"
    list_per_page = 10
    ordering = [
        "title",
    ]
    list_display = ("title",)
    empty_value_display = "-"
    search_fields = ("title",)


class OnlineWorshipModelAdmin(ModelAdmin):
    model = OnlineWorship
    menu_icon = "home"
    menu_label = "Online Worship"
    list_per_page = 10
    ordering = [
        "title",
    ]
    list_display = ("title",)
    empty_value_display = "-"
    search_fields = ("title",)


class CommunityResourcesGroup(ModelAdminGroup):
    menu_label = "Resources"
    menu_icon = "snippet"
    menu_order = 300
    items = (CommunityDirectoryModelAdmin, OnlineWorshipModelAdmin)


modeladmin_register(CommunityResourcesGroup)
