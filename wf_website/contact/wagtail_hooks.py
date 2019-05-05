from django.utils.html import format_html_join
from django.conf import settings

from wagtail.contrib.modeladmin.options import ModelAdmin, modeladmin_register
from wagtail.core import hooks

from .models import Contact


class ContactModelAdmin(ModelAdmin):
    model = Contact
    menu_icon = "mail"
    menu_label = "Contacts"
    menu_order = 200
    add_to_settings_menu = False
    exclude_from_explorer = False
    list_per_page = 10
    ordering = ["family_name", "given_name"]
    list_display = ("given_name", "family_name", "full_name", "contact_type")
    empty_value_display = "-"
    search_fields = ("given_name", "family_name")
    list_filter = ("contact_type",)


modeladmin_register(ContactModelAdmin)


@hooks.register('insert_editor_js')
def editor_js():
    js_files = [
        'contact/js/contact_slug.js',
    ]
    js_includes = format_html_join('\n', '<script src="{0}{1}"></script>',
                                   ((settings.STATIC_URL, filename)
                                    for filename in js_files)
                                   )
    return js_includes
