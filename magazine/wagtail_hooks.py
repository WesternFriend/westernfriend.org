from django.urls import reverse
from wagtail.contrib.modeladmin.helpers import PageAdminURLHelper, PageButtonHelper
from wagtail.contrib.modeladmin.options import (
    ModelAdmin,
    ModelAdminGroup,
    modeladmin_register,
)

from .models import MagazineDepartment, MagazineIssue, ArchiveIssue


class MagazineIssueAdminURLHelper(PageAdminURLHelper):
    def get_action_url(self, action, *args, **kwargs):
        if action == "add-child":
            url_name = "wagtailadmin_pages:add_subpage"
            target_url = reverse(url_name, args=args, kwargs=kwargs)

            return target_url

        # for every other case - just call the parent method
        return super().get_action_url(action, *args, **kwargs)


class MagazineIssueButtonHelperClass(PageButtonHelper):

    add_child_button_classnames = ["add-child"]

    def add_child_button(self, pk, classnames_add=[], classnames_exclude=[]):
        classnames = self.add_child_button_classnames + classnames_add
        final_classnames = self.finalise_classname(classnames, classnames_exclude)

        return {
            "url": self.url_helper.get_action_url("add-child", pk),
            "label": "Add Article",
            "classname": final_classnames,
            "title": "Add article under this %s" % self.verbose_name,
        }

    def get_buttons_for_obj(
        self, obj, exclude=[], classnames_add=[], classnames_exclude=[]
    ):
        # call the parent class method to get the default set of buttons
        buttons = super().get_buttons_for_obj(
            obj, exclude, classnames_add, classnames_exclude
        )

        # set up some variables to do user checks and also get the primary key (id)
        permission_helper = self.permission_helper
        user = self.request.user
        pk = getattr(obj, self.opts.pk.attname)

        # many existing permission helpers are already available - see wagtail/contrib/modeladmin/helpers/permission.py
        if "add-child" not in exclude and permission_helper.user_can_create(user):
            add_child_button = self.add_child_button(
                pk, classnames_add, classnames_exclude
            )
            buttons.append(add_child_button)

        return buttons


class MagazineIssueModelAdmin(ModelAdmin):
    model = MagazineIssue
    menu_icon = "fa-book"
    menu_label = "Issues"
    list_per_page = 10
    ordering = [
        "-publication_date",
    ]
    list_display = ("title", "publication_date")
    list_filter = ("publication_date",)
    empty_value_display = "-"
    search_fields = ("title",)

    button_helper_class = (
        MagazineIssueButtonHelperClass  # added to enable custom button generation
    )
    url_helper_class = (
        MagazineIssueAdminURLHelper  # added to enable custom url generation
    )


class ArchiveIssueModelAdmin(ModelAdmin):
    model = ArchiveIssue
    menu_icon = "fa-newspaper-o"
    menu_label = "Archive Issues"
    list_per_page = 10
    ordering = [
        "publication_date",
    ]
    list_display = ("title", "publication_date")
    empty_value_display = "-"
    search_fields = ("title",)


class MagazineDepartmentModelAdmin(ModelAdmin):
    model = MagazineDepartment
    menu_icon = "folder-inverse"
    menu_label = "Departments"
    menu_order = 200
    add_to_settings_menu = False
    exclude_from_explorer = False
    list_per_page = 10
    list_display = ("title",)
    search_fields = ("title",)


class MagazineGroup(ModelAdminGroup):
    menu_label = "Magazine"
    menu_icon = "fa-book"
    menu_order = 100
    items = (
        MagazineIssueModelAdmin,
        ArchiveIssueModelAdmin,
        MagazineDepartmentModelAdmin,
    )


modeladmin_register(MagazineGroup)
