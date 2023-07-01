from django.http import HttpRequest
from django.utils import timezone

from wagtail.admin.panels import FieldPanel
from wagtail.fields import RichTextField
from wagtail.models import Page

from events.models import Event
from magazine.models import MagazineIssue


class HomePage(Page):
    intro = RichTextField(blank=True)

    content_panels = Page.content_panels + [
        FieldPanel("intro", classname="full"),
    ]

    subpage_types: list[str] = [
        "community.CommunityPage",
        "documents.PublicBoardDocumentIndexPage",
        "documents.MeetingDocumentIndexPage",
        "donations.DonatePage",
        "events.EventsIndexPage",
        "facets.FacetIndexPage",
        "forms.ContactFormPage",
        "library.LibraryIndexPage",
        "magazine.MagazineIndexPage",
        "memorials.MemorialIndexPage",
        "news.NewsIndexPage",
        "store.StoreIndexPage",
        "subscription.ManageSubscriptionPage",
        "subscription.SubscriptionIndexPage",
        "wf_pages.MollyWingateBlogIndexPage",
        "wf_pages.WfPage",
        "wf_pages.WfPageCollectionIndexPage",
    ]

    max_count = 1

    def get_context(self, request: HttpRequest, *args: tuple, **kwargs: dict) -> dict:
        context = super().get_context(request)

        context["current_issue"] = (
            MagazineIssue.objects.live().order_by("-publication_date").first()
        )

        context["featured_events"] = (
            Event.objects.live()
            .filter(
                start_date__gte=timezone.now(),
                is_featured=True,
            )
            .order_by("start_date")[:3]
        )

        return context
