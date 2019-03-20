from wagtail.contrib.modeladmin.options import ModelAdmin, modeladmin_register

from .models import Contact


class ContactModelAdmin(ModelAdmin):
    model = Contact
    menu_icon = "mail"
    menu_label = "Contacts"
    menu_order = 200
    add_to_settings_menu = False
    exclude_from_explorer = False
    list_per_page = 10
    # ordering = [
    #     "family_name",
    #     "given_name",
    # ]
    list_display = ("given_name", "family_name", "full_name", "slug")
    # empty_value_display = '-'
    # search_fields = (
    #     'given_name',
    #     'family_name',
    # )


modeladmin_register(ContactModelAdmin)
