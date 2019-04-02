from wagtail.contrib.modeladmin.options import ModelAdmin, modeladmin_register

from .models import Contact, ContactType


class ContactModelAdmin(ModelAdmin):
    model = ContactType
    menu_icon = "mail"
    menu_label = "Contact Types"
    menu_order = 300
    add_to_settings_menu = True
    exclude_from_explorer = False
    list_per_page = 10

    # list_display = ("given_name", "family_name", "full_name", "slug")
    # search_fields = (
    #     'given_name',
    #     'family_name',
    # )


class ContactTypeModelAdmin(ModelAdmin):
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
modeladmin_register(ContactTypeModelAdmin)
