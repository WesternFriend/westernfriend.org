from django.urls import reverse
from django.utils.html import format_html
from wagtail_modeladmin.helpers import PageAdminURLHelper, PageButtonHelper
from wagtail_modeladmin.mixins import ThumbnailMixin
from wagtail_modeladmin.options import (
    ModelAdmin,
    ModelAdminGroup,
    modeladmin_register,
)

from .models import ArchiveIssue, MagazineDepartment, MagazineIssue


class MagazineIssueAdminURLHelper(PageAdminURLHelper):
    def get_action_url(
        self,
        action,
        *args,
        **kwargs,
    ):  # pragma: no cover
        if action == "add-child":
            url_name = "wagtailadmin_pages:add_subpage"
            target_url = reverse(url_name, args=args, kwargs=kwargs)

            return target_url

        # for every other case - just call the parent method
        return super().get_action_url(action, *args, **kwargs)


class MagazineIssueButtonHelperClass(PageButtonHelper):
    add_child_button_classnames = ["add-child"]

    def add_child_button(
        self,
        pk,
        classnames_add=None,
        classnames_exclude=None,
    ):  # pragma: no cover
        if classnames_add is None:
            classnames_add = []
        if classnames_exclude is None:
            classnames_exclude = []

        classnames = self.add_child_button_classnames + classnames_add
        final_classnames = self.finalise_classname(classnames, classnames_exclude)

        return {
            "url": self.url_helper.get_action_url("add-child", pk),
            "label": "Add Article",
            "classname": final_classnames,
            "title": f"Add article under this {self.verbose_name}",
        }

    def get_buttons_for_obj(
        self,
        obj,
        exclude=None,
        classnames_add=None,
        classnames_exclude=None,
    ):  # pragma: no cover
        if exclude is None:
            exclude = ([],)
        if classnames_add is None:
            classnames_add = ([],)
        if classnames_exclude is None:
            classnames_exclude = []

        # call the parent class method to get the default set of buttons
        buttons = super().get_buttons_for_obj(
            obj,
            exclude,
            classnames_add,
            classnames_exclude,
        )

        # set up some variables to do user checks and also get the primary key (id)
        permission_helper = self.permission_helper
        user = self.request.user
        pk = getattr(obj, self.opts.pk.attname)

        # many existing permission helpers are already available
        # - see wagtail/contrib/modeladmin/helpers/permission.py
        if "add-child" not in exclude and permission_helper.user_can_create(user):
            add_child_button = self.add_child_button(
                pk,
                classnames_add,
                classnames_exclude,
            )
            buttons.append(add_child_button)

        return buttons


class MagazineIssueModelAdmin(ThumbnailMixin, ModelAdmin):
    model = MagazineIssue
    menu_icon = "doc-full-inverse"
    menu_label = "Issues"
    list_per_page = 10
    ordering = [
        "-publication_date",
    ]
    list_display = (
        "admin_thumb",
        "title",
        "publication_date",
        "live",
        "view_articles",
        "add_article",
    )
    list_display_add_buttons = "title"
    thumb_image_field_name = "cover_image"
    thumb_image_filter_spec = "height-333"
    thumb_col_header_text = "Cover"
    thumb_default = "https://lorempixel.com/100/100"
    list_filter = ("publication_date",)
    empty_value_display = "-"
    search_fields = ("title",)

    button_helper_class = (
        MagazineIssueButtonHelperClass  # added to enable custom button generation
    )
    url_helper_class = (
        MagazineIssueAdminURLHelper  # added to enable custom url generation
    )

    def add_article(
        self,
        obj,
    ):  # pragma: no cover
        url_name = "wagtailadmin_pages:add_subpage"
        url = reverse(url_name, args=[obj.id])

        return format_html(
            f'<a href="{url}" class="button button-small button-secondary">Add Article</a>',  # noqa: E501
        )

    def view_articles(
        self,
        obj,
    ):  # pragma: no cover
        url_name = "wagtailadmin_explore"
        url = reverse(url_name, args=[obj.id])

        return format_html(
            f'<a href="{url}" class="button button-small button-secondary">View Articles</a>',  # noqa: E501
        )


class ArchiveIssueModelAdmin(ModelAdmin):
    model = ArchiveIssue
    menu_icon = "doc-full"
    menu_label = "Archive Issues"
    list_per_page = 10
    ordering = [
        "publication_date",
    ]
    list_display = (
        "title",
        "publication_date",
        "internet_archive_identifier",
    )
    empty_value_display = "-"
    search_fields = (
        "title",
        "internet_archive_identifier",
    )


class MagazineDepartmentModelAdmin(ModelAdmin):
    model = MagazineDepartment
    menu_icon = "tag"
    menu_label = "Departments"
    menu_order = 200
    add_to_settings_menu = False
    exclude_from_explorer = False
    list_per_page = 10
    list_display = ("title",)
    search_fields = ("title",)


class MagazineGroup(ModelAdminGroup):
    menu_label = "Magazine"
    menu_icon = "tablet-alt"
    menu_order = 100
    items = (
        MagazineIssueModelAdmin,
        ArchiveIssueModelAdmin,
        MagazineDepartmentModelAdmin,
    )


modeladmin_register(MagazineGroup)
