import django_filters
from wagtail.admin.filters import DateRangePickerWidget
from wagtail.admin.ui.tables import Column
from wagtail.admin.ui.tables.pages import BulkActionsColumn, PageTitleColumn
from wagtail.admin.viewsets.base import ViewSetGroup
from wagtail.admin.viewsets.pages import PageListingViewSet

from .models import (
    Audience,
    Genre,
    Medium,
    TimePeriod,
    Topic,
    LibraryItem,
)


class AudienceViewSet(PageListingViewSet):
    model = Audience
    menu_label = "Audiences"
    icon = "tag"
    name = "audiences"
    columns = [
        BulkActionsColumn(
            "id",
        ),
        PageTitleColumn(
            "title",
            label="Title",
            sort_key="title",
            classname="title",
        ),
    ]
    search_fields = ["title"]
    ordering = ["title"]


class GenreViewSet(PageListingViewSet):
    model = Genre
    menu_label = "Genres"
    icon = "tag"
    name = "genres"
    columns = [
        BulkActionsColumn(
            "id",
        ),
        PageTitleColumn(
            "title",
            label="Title",
            sort_key="title",
            classname="title",
        ),
    ]
    search_fields = ["title"]
    ordering = ["title"]


class MediumViewSet(PageListingViewSet):
    model = Medium
    menu_label = "Mediums"
    icon = "tag"
    name = "mediums"
    columns = [
        BulkActionsColumn(
            "id",
        ),
        PageTitleColumn(
            "title",
            label="Title",
            sort_key="title",
            classname="title",
        ),
    ]
    search_fields = ["title"]
    ordering = ["title"]


class TimePeriodViewSet(PageListingViewSet):
    model = TimePeriod
    menu_label = "Time Periods"
    icon = "tag"
    name = "time_periods"
    columns = [
        BulkActionsColumn(
            "id",
        ),
        PageTitleColumn(
            "title",
            label="Title",
            sort_key="title",
            classname="title",
        ),
    ]
    search_fields = ["title"]
    ordering = ["title"]


class TopicViewSet(PageListingViewSet):
    model = Topic
    menu_label = "Topics"
    icon = "tag"
    name = "topics"
    columns = [
        BulkActionsColumn(
            "id",
        ),
        PageTitleColumn(
            "title",
            label="Title",
            sort_key="title",
            classname="title",
        ),
    ]
    search_fields = ["title"]
    ordering = ["title"]


class LibraryItemFilterSet(PageListingViewSet.filterset_class):
    publication_date = django_filters.DateFromToRangeFilter(
        label="Publication Date",
        widget=DateRangePickerWidget,
    )

    class Meta:
        model = LibraryItem
        fields = [
            "publication_date",
            "item_audience",
            "item_genre",
            "item_medium",
            "item_time_period",
            "live",
        ]


class LibraryItemViewSet(PageListingViewSet):
    model = LibraryItem
    menu_label = "Items"
    icon = "list-ul"
    name = "library_items"
    columns = [
        BulkActionsColumn(
            "id",
        ),
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
    filterset_class = LibraryItemFilterSet


class LibraryViewSetGroup(ViewSetGroup):
    menu_label = "Library"
    menu_icon = "clipboard-list"
    menu_order = 200
    items = (
        AudienceViewSet,
        GenreViewSet,
        MediumViewSet,
        TimePeriodViewSet,
        TopicViewSet,
        LibraryItemViewSet,
    )
