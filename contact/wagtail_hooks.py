from wagtail import hooks
from wagtail.admin.menu import MenuItem

from .models import Meeting, Organization, Person
from .views import ContactPublicationStatsView, ContactViewSetGroup


@hooks.register("construct_queryset")
def prefetch_contact_related(queryset):
    """Prefetch related objects for contact models."""
    contact_models = [Meeting, Organization, Person]
    if queryset.model in contact_models:
        return queryset.prefetch_related(
            "articles_authored__article",
            "archive_articles_authored__article",
            "library_items_authored__library_item",
            "memorial_minutes__memorial_person",
            "presiding_clerks__person",
        )

    return queryset


@hooks.register("register_admin_viewset")
def register_contact_viewset_group():
    return ContactViewSetGroup()


@hooks.register("register_reports_menu_item")
def register_contact_publication_stats_menu_item():
    """Register the contact publication statistics report in the reports menu."""
    return MenuItem(
        "Publication Stats",
        "/admin/reports/contact-publication-stats/",
        icon_name="doc-full",
    )


@hooks.register("register_admin_urls")
def register_contact_publication_stats_url():
    """Register the URL for the contact publication statistics report."""
    from django.urls import path

    return [
        path(
            "reports/contact-publication-stats/",
            ContactPublicationStatsView.as_view(),
            name="contact_publication_stats",
        ),
        path(
            "reports/contact-publication-stats/results/",
            ContactPublicationStatsView.as_view(results_only=True),
            name="contact_publication_stats_results",
        ),
    ]
