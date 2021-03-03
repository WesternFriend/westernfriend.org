from wagtail.contrib.modeladmin.options import (
    ModelAdmin,
    modeladmin_register
)

from library.models import LibraryItem

@modeladmin_register
class LibraryItemModelAdmin(ModelAdmin):
    model = LibraryItem
    menu_icon = "media"
    menu_label = "Media library"
    list_per_page = 10
    list_display = ("title", "item_audience", "item_genre", "item_medium", "item_time_period",)
    search_fields = ("title")
