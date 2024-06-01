import django_filters
from wagtail.admin.filters import DateRangePickerWidget
from wagtail.admin.ui.tables import Column, TitleColumn
from wagtail.admin.viewsets.pages import PageListingViewSet

from .models import PublicBoardDocument, MeetingDocument


class PublicBoardDocumentFilterSet(PageListingViewSet.filterset_class):
    publication_date = django_filters.DateFromToRangeFilter(
        label="Publication Date",
        widget=DateRangePickerWidget,
    )

    class Meta:
        model = PublicBoardDocument
        fields = [
            "publication_date",
            "category",
            "live",
        ]


class PublicBoardDocumentViewSet(PageListingViewSet):
    model = PublicBoardDocument
    menu_label = "Public Board Documents"
    icon = "doc-full"
    name = "public_board_documents"
    columns = [
        TitleColumn(
            "title",
            label="Title",
            sort_key="title",
        ),
        Column(
            "publication_date",
            label="Publication Date",
            sort_key="publication_date",
        ),
    ]
    search_fields = ["title"]
    ordering = ["-publication_date"]
    filterset_class = PublicBoardDocumentFilterSet


class MeetingDocumentFilterSet(PageListingViewSet.filterset_class):
    publication_date = django_filters.DateFromToRangeFilter(
        label="Publication Date",
        widget=DateRangePickerWidget,
    )

    class Meta:
        model = MeetingDocument
        fields = [
            "publication_date",
            "publishing_meeting",
            "document_type",
            "live",
        ]


class MeetingDocumentViewSet(PageListingViewSet):
    model = MeetingDocument
    menu_label = "Meeting Documents"
    icon = "doc-full"
    name = "meeting_documents"
    columns = [
        Column(
            "title",
            label="Title",
            sort_key="title",
        ),
        Column(
            "publication_date",
            label="Publication Date",
            sort_key="publication_date",
        ),
        Column(
            "publishing_meeting",
            label="Publishing Meeting",
            sort_key="publishing_meeting",
        ),
        Column(
            "document_type",
            label="Document Type",
            sort_key="document_type",
        ),
    ]
    search_fields = ["title"]
    ordering = ["-publication_date"]
    filterset_class = MeetingDocumentFilterSet
