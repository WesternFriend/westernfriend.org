from django.db.models import OuterRef, Subquery
from django.utils.html import format_html
from wagtail.admin.filters import WagtailFilterSet
from wagtail.admin.ui.tables import Column
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


class PublicationColumn(Column):
    """Column for displaying publication information."""

    cell_template_name = "wagtailadmin/tables/publication_count_cell.html"

    def get_cell_context_data(self, instance, parent_context):
        context = super().get_cell_context_data(instance, parent_context)
        context.update(
            {
                "article_count": getattr(instance, "article_count", 0),
                "last_published_at": getattr(instance, "last_published_at", None),
            },
        )
        return context


class PersonViewSet(PageListingViewSet):
    model = Person
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
        "article_count",
        "last_published_at",
    ]

    def get_queryset(self, request):
        from contact.models import ContactPublicationStatistics

        queryset = super().get_queryset(request)

        # Add publication statistics via subquery
        article_count_subquery = ContactPublicationStatistics.objects.filter(
            contact=OuterRef("pk"),
        ).values("article_count")[:1]

        last_published_subquery = ContactPublicationStatistics.objects.filter(
            contact=OuterRef("pk"),
        ).values("last_published_at")[:1]

        queryset = queryset.annotate(
            article_count=Subquery(article_count_subquery),
            last_published_at=Subquery(last_published_subquery),
        )

        return queryset

    def article_count(self, obj):
        """Display the article count with a link to detailed publication stats."""
        if hasattr(obj, "article_count") and obj.article_count:
            return format_html(
                '<a href="/admin/reports/contact-publication-stats/?contact_type=person">{}</a>',
                obj.article_count,
            )
        return 0

    article_count.short_description = "Articles"
    article_count.admin_order_field = "article_count"

    def last_published_at(self, obj):
        """Display the date when the contact last published an article."""
        return obj.last_published_at

    last_published_at.short_description = "Last Published"
    last_published_at.admin_order_field = "last_published_at"


class MeetingFilterSet(PageListingViewSet.filterset_class):
    class Meta:
        model = Meeting
        fields = [
            "meeting_type",
        ]


class MeetingViewSet(PageListingViewSet):
    model = Meeting
    menu_label = "Meetings"
    icon = "home"
    name = "meetings"
    search_fields = ["title"]
    filterset_class = MeetingFilterSet
    ordering = ["title"]

    list_display = [
        "title",
        "meeting_type",
        "article_count",
        "last_published_at",
    ]

    def get_queryset(self, request):
        from contact.models import ContactPublicationStatistics

        queryset = super().get_queryset(request)

        # Add publication statistics via subquery
        article_count_subquery = ContactPublicationStatistics.objects.filter(
            contact=OuterRef("pk"),
        ).values("article_count")[:1]

        last_published_subquery = ContactPublicationStatistics.objects.filter(
            contact=OuterRef("pk"),
        ).values("last_published_at")[:1]

        queryset = queryset.annotate(
            article_count=Subquery(article_count_subquery),
            last_published_at=Subquery(last_published_subquery),
        )

        return queryset

    def article_count(self, obj):
        """Display the article count with a link to detailed publication stats."""
        if hasattr(obj, "article_count") and obj.article_count:
            return format_html(
                '<a href="/admin/reports/contact-publication-stats/?contact_type=meeting">{}</a>',
                obj.article_count,
            )
        return 0

    article_count.short_description = "Articles"
    article_count.admin_order_field = "article_count"

    def last_published_at(self, obj):
        """Display the date when the contact last published an article."""
        return obj.last_published_at

    last_published_at.short_description = "Last Published"
    last_published_at.admin_order_field = "last_published_at"


class OrganizationViewSet(PageListingViewSet):
    model = Organization
    menu_label = "Organizations"
    icon = "group"
    name = "organizations"
    search_fields = ["title"]
    ordering = ["title"]

    list_display = [
        "title",
        "article_count",
        "last_published_at",
    ]

    def get_queryset(self, request):
        from contact.models import ContactPublicationStatistics

        queryset = super().get_queryset(request)

        # Add publication statistics via subquery
        article_count_subquery = ContactPublicationStatistics.objects.filter(
            contact=OuterRef("pk"),
        ).values("article_count")[:1]

        last_published_subquery = ContactPublicationStatistics.objects.filter(
            contact=OuterRef("pk"),
        ).values("last_published_at")[:1]

        queryset = queryset.annotate(
            article_count=Subquery(article_count_subquery),
            last_published_at=Subquery(last_published_subquery),
        )

        return queryset

    def article_count(self, obj):
        """Display the article count with a link to detailed publication stats."""
        if hasattr(obj, "article_count") and obj.article_count:
            return format_html(
                '<a href="/admin/reports/contact-publication-stats/?contact_type=organization">{}</a>',
                obj.article_count,
            )
        return 0

    article_count.short_description = "Articles"
    article_count.admin_order_field = "article_count"

    def last_published_at(self, obj):
        """Display the date when the contact last published an article."""
        return obj.last_published_at

    last_published_at.short_description = "Last Published"
    last_published_at.admin_order_field = "last_published_at"


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
    class Meta:
        model = ContactPublicationStatistics
        fields = ["contact_type", "article_count"]


class ContactPublicationStatsView(ReportView):
    """Admin view showing publication statistics for all contacts."""

    page_title = "Contact Publication Statistics"
    header_icon = "user"
    filterset_class = ContactPublicationStatsFilterSet

    export_filename = "contact_publication_stats"
    export_headings = {
        "contact": "Contact Name",
        "contact_type": "Contact Type",
        "article_count": "Article Count",
        "last_published_at": "Last Published",
    }

    list_export = [
        "contact",
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
