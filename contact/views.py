import django_filters
from django.db.models import F
from django.urls import reverse
from django.utils.html import format_html
from django.utils.http import urlencode
from wagtail.admin.filters import DateRangePickerWidget, WagtailFilterSet
from wagtail.admin.ui.tables import Column, DateColumn
from wagtail.admin.views.pages.listing import IndexView
from wagtail.admin.views.reports import ReportView
from wagtail.admin.viewsets.base import ViewSetGroup
from wagtail.admin.viewsets.pages import PageListingViewSet

from memorials.views import MemorialViewSet

from .models import (
    ContactPublicationStatistics,
    Meeting,
    Organization,
    Person,
)


class ArticleCountColumn(Column):
    """Article count linking to the publication stats report for the contact type."""

    def __init__(self, contact_type, **kwargs):
        super().__init__(
            "article_count",
            label="Articles",
            sort_key="article_count",
            **kwargs,
        )
        self.contact_type = contact_type

    def get_value(self, instance):
        article_count = super().get_value(instance)
        if not article_count:
            return 0
        url = reverse("contact_publication_stats")
        return format_html(
            '<a href="{}?{}">{}</a>',
            url,
            urlencode({"contact_type": self.contact_type}),
            article_count,
        )


class ContactIndexView(IndexView):
    """Page listing annotated with each contact's publication statistics."""

    def get_base_queryset(self):
        return (
            super()
            .get_base_queryset()
            .annotate(
                article_count=F("publication_statistics__article_count"),
                last_article_published_at=F(
                    "publication_statistics__last_published_at",
                ),
            )
        )


def publication_columns(contact_type):
    return [
        ArticleCountColumn(contact_type),
        DateColumn(
            "last_article_published_at",
            label="Last Published",
            sort_key="last_article_published_at",
        ),
    ]


class PersonViewSet(PageListingViewSet):
    model = Person
    index_view_class = ContactIndexView
    menu_label = "People"
    name = "people"
    icon = "user"
    search_fields = ["given_name", "family_name"]
    # Tried to add ordering to the columns, but it didn't work.
    # https://stackoverflow.com/questions/78563124/how-to-specify-ordering-for-wagtal-pagelistingviewset
    ordering = ["family_name", "given_name"]

    list_display = [
        "title",
        "given_name",
        "family_name",
        *publication_columns(ContactPublicationStatistics.ContactType.PERSON),
    ]


class MeetingFilterSet(PageListingViewSet.filterset_class):
    class Meta:
        model = Meeting
        fields = [
            "meeting_type",
        ]


class MeetingViewSet(PageListingViewSet):
    model = Meeting
    index_view_class = ContactIndexView
    menu_label = "Meetings"
    icon = "home"
    name = "meetings"
    search_fields = ["title"]
    filterset_class = MeetingFilterSet
    ordering = ["title"]

    list_display = [
        "title",
        "meeting_type",
        *publication_columns(ContactPublicationStatistics.ContactType.MEETING),
    ]


class OrganizationViewSet(PageListingViewSet):
    model = Organization
    index_view_class = ContactIndexView
    menu_label = "Organizations"
    icon = "group"
    name = "organizations"
    search_fields = ["title"]
    ordering = ["title"]

    list_display = [
        "title",
        *publication_columns(ContactPublicationStatistics.ContactType.ORGANIZATION),
    ]


class ContactViewSetGroup(ViewSetGroup):
    menu_label = "Contacts"
    menu_icon = "group"
    menu_order = 100
    items = [
        PersonViewSet,
        MeetingViewSet,
        OrganizationViewSet,
        MemorialViewSet,
    ]


class ContactPublicationStatsFilterSet(WagtailFilterSet):
    last_published_at = django_filters.DateFromToRangeFilter(
        label="Last Published",
        widget=DateRangePickerWidget,
    )

    class Meta:
        model = ContactPublicationStatistics
        fields = ["contact_type", "article_count", "last_published_at"]


class ContactPublicationStatsView(ReportView):
    """Admin view showing publication statistics for all contacts."""

    page_title = "Contact Publication Statistics"
    header_icon = "user"
    filterset_class = ContactPublicationStatsFilterSet
    results_template_name = "contact/reports/contact_publication_stats.html"

    # Add the required URL names
    index_url_name = "contact_publication_stats"
    index_results_url_name = "contact_publication_stats_results"

    export_filename = "contact_publication_stats"
    export_headings = {
        "contact__title": "Contact Name",
        "contact_type": "Contact Type",
        "article_count": "Articles",
        "last_published_at": "Last Published",
    }

    list_export = [
        "contact__title",
        "contact_type",
        "article_count",
        "last_published_at",
    ]

    def get_queryset(self):
        """Get queryset of contact publication statistics."""
        return (
            ContactPublicationStatistics.objects.all()
            .select_related("contact")
            .order_by("-article_count", "-last_published_at")
        )
