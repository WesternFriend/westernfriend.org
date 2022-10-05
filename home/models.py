from wagtail.admin.edit_handlers import FieldPanel
from wagtail.core.fields import RichTextField
from wagtail.core.models import Page

from magazine.models import MagazineIssue


class HomePage(Page):
    intro = RichTextField(blank=True)

    content_panels = Page.content_panels + [
        FieldPanel("intro", classname="full"),
    ]

    subpage_types = [
        "community.CommunityPage",
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
        "wf_pages.WfPage",
        "wf_pages.WfPageCollectionIndexPage",
    ]

    max_count = 1

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request)
        # pylint: disable=E501
        context["current_issue"] = (
            MagazineIssue.objects.live().order_by("-publication_date").first()
        )

        return context
