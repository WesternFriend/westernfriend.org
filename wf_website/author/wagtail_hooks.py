from wagtail.contrib.modeladmin.options import (
    ModelAdmin,
    modeladmin_register,
)
from .models import Author

class AuthorModelAdmin(ModelAdmin):
    model = Author
    menu_icon = 'user'
    menu_label = 'Authors'
    menu_order = 100
    add_to_settings_menu = False
    exclude_from_explorer = False
    list_per_page = 10
    ordering = [
        "family_name",
        "given_name",
    ]
    list_display = (
        'given_name',
        'family_name',
    )
    empty_value_display = '-'
    search_fields = (
        'given_name',
        'family_name',
    )

modeladmin_register(AuthorModelAdmin)


