from wagtail.contrib.modeladmin.options import (
    ModelAdmin,
    modeladmin_register
)

from memorials.models import Memorial


class MemorialModelAdmin(ModelAdmin):
    """Memorial model admin."""

    model = Memorial
    menu_label = "Memorials"
    menu_icon = "fa-circle-o-notch"
    menu_order = 295
    add_to_settings_menu = False
    exclude_from_explorer = False
    list_display = (
        "full_name",
        "memorial_meeting"
    )
    search_fields = (
        "user",
        "given_name",
        "family_name",
    )


modeladmin_register(MemorialModelAdmin)
