from django.views.generic import DetailView
import django_filters
from wagtail.admin.filters import DateRangePickerWidget
from wagtail.admin.viewsets.base import ViewSetGroup
from wagtail.admin.viewsets.pages import PageListingViewSet
from wagtail.admin.ui.tables import DateColumn
from wagtail.admin.ui.tables.pages import (
    BulkActionsColumn,
    PageTitleColumn,
    PageStatusColumn,
)
from .models import (
    ArchiveIssue,
    MagazineDepartment,
    MagazineIssue,
)


class MagazineDepartmentDetail(DetailView):
    model = MagazineDepartment
    context_object_name = "department"

    template_name = "magazine/magazine_department_detail.html"


class MagazineIssueFilterSet(PageListingViewSet.filterset_class):
    publication_date = django_filters.DateFromToRangeFilter(
        label="Publication Date",
        widget=DateRangePickerWidget,
    )

    class Meta:
        model = MagazineIssue
        fields = [
            "publication_date",
        ]


class ArchiveIssueViewSet(PageListingViewSet):
    model = ArchiveIssue
    menu_label = "Archive Issues"
    icon = "doc-full"
    add_to_admin_menu = True
    columns = [
        PageTitleColumn(
            "title",
            label="Title",
            sort_key="title",
        ),
        DateColumn(
            "publication_date",
            label="Publication Date",
            sort_key="publication_date",
        ),
        PageStatusColumn(
            "live",
            label="Live",
            sort_key="live",
        ),
        BulkActionsColumn(
            "bulk_actions",
            label="Bulk Actions",
        ),
    ]
    search_fields = (
        "title",
        "internet_archive_identifier",
    )


archive_issue_viewset = ArchiveIssueViewSet("archive_issues")


class MagazineDepartmentViewSet(PageListingViewSet):
    model = MagazineDepartment
    menu_label = "Departments"
    icon = "tag"
    add_to_admin_menu = True
    columns = [
        PageTitleColumn(
            "title",
            label="Title",
            sort_key="title",
        ),
        BulkActionsColumn(
            "bulk_actions",
            label="Bulk Actions",
        ),
    ]
    search_fields = ("title",)


magazine_department_viewset = MagazineDepartmentViewSet("magazine_departments")


class MagazineIssueViewSet(PageListingViewSet):
    model = MagazineIssue
    menu_label = "Issues"
    icon = "doc-full-inverse"
    add_to_admin_menu = True
    search_fields = ("title",)
    filterset_class = MagazineIssueFilterSet


magazine_issue_viewset = MagazineIssueViewSet("magazine_issues")


class MagazineViewSetGroup(ViewSetGroup):
    menu_label = "Magazine"
    menu_icon = "tablet-alt"
    menu_order = 100
    items = (
        archive_issue_viewset,
        magazine_department_viewset,
        magazine_issue_viewset,
    )
