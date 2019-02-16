from wagtail.contrib.modeladmin.options import (
    ModelAdmin,
    modeladmin_register,
)

from .models import MagazineDepartment


class MagazineDepartmentModelAdmin(ModelAdmin):
    model = MagazineDepartment
    menu_icon = 'folder-inverse'
    menu_label = 'Departments'
    menu_order = 200
    add_to_settings_menu = False
    exclude_from_explorer = False
    list_per_page = 10
    list_display = (
        'name',
    )
    search_fields = (
        'name',
    )


modeladmin_register(MagazineDepartmentModelAdmin)
