from wagtail.contrib.modeladmin.options import ModelAdmin, modeladmin_register

from events.models import Event


class EventModelAdmin(ModelAdmin):
    model = Event
    menu_icon = "date"
    menu_label = "Events"
    menu_order = 200
    add_to_settings_menu = False
    exclude_from_explorer = False
    list_per_page = 10
    ordering = ["start_date"]
    list_display = (
        "title",
        "start_date",
        "end_date",
        "live",
    )
    empty_value_display = "-"
    search_fields = ("title", "description")
    list_filter = ("start_date",)


modeladmin_register(EventModelAdmin)
