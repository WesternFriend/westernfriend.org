import django_filters
from wagtail.admin.filters import DateRangePickerWidget
from wagtail.admin.ui.tables import Column
from wagtail.admin.ui.tables.pages import PageTitleColumn
from wagtail.admin.viewsets.pages import PageListingViewSet


from .models import MollyWingateBlogPage


class MollyWingateBlogPageFilterSet(PageListingViewSet.filterset_class):
    publication_date = django_filters.DateFromToRangeFilter(
        label="Publication Date",
        widget=DateRangePickerWidget,
    )

    class Meta:
        model = MollyWingateBlogPage
        fields = [
            "publication_date",
            "live",
        ]


class MollyWingateBlogPageViewSet(PageListingViewSet):
    model = MollyWingateBlogPage
    menu_label = "Molly Wingate Blog Pages"
    icon = "list-ul"
    name = "molly_wingate_blog_pages"
    columns = [
        PageTitleColumn(
            "title",
            label="Title",
            sort_key="title",
            classname="title",
        ),
        Column(
            "publication_date",
            label="Publication Date",
            sort_key="publication_date",
        ),
    ]
    search_fields = ["title"]
    ordering = ["-publication_date"]
    filterset_class = MollyWingateBlogPageFilterSet
