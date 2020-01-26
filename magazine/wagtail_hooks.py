from wagtail.contrib.modeladmin.options import (
    ModelAdmin,
    ModelAdminGroup,
    modeladmin_register
)

from .models import MagazineDepartment, MagazineIssue, ArchiveIssue


class MagazineIssueModelAdmin(ModelAdmin):
    model = MagazineIssue
    menu_icon = "fa-book"
    menu_label = "Issues"
    list_per_page = 10
    ordering = ["publication_date", ]
    list_display = ("title", "publication_date")
    list_filter = ("first_published_at", )
    empty_value_display = "-"
    search_fields = ("title",)


class ArchiveIssueModelAdmin(ModelAdmin):
    model = ArchiveIssue
    menu_icon = "fa-newspaper-o"
    menu_label = "Archive Issues"
    list_per_page = 10
    ordering = ["publication_date", ]
    list_display = ("title", "publication_date")
    empty_value_display = "-"
    search_fields = ("title",)


class MagazineDepartmentModelAdmin(ModelAdmin):
    model = MagazineDepartment
    menu_icon = 'folder-inverse'
    menu_label = 'Departments'
    menu_order = 200
    add_to_settings_menu = False
    exclude_from_explorer = False
    list_per_page = 10
    list_display = (
        'title',
    )
    search_fields = (
        'title',
    )


class MagazineGroup(ModelAdminGroup):
    menu_label = "Magazine"
    menu_icon = "fa-book"
    menu_order = 100
    items = (MagazineIssueModelAdmin, ArchiveIssueModelAdmin, MagazineDepartmentModelAdmin)


modeladmin_register(MagazineGroup)
