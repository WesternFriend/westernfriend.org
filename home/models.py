from django.db import models
from modelcluster.fields import ParentalKey
from wagtail.admin.edit_handlers import FieldPanel, InlinePanel
from wagtail.core.fields import RichTextField
from wagtail.core.models import Page, Orderable

from magazine.models import MagazineIssue, MagazineArticle


class HomePage(Page):
    intro = RichTextField(blank=True)

    content_panels = Page.content_panels + [
        FieldPanel("intro", classname="full"),
        InlinePanel(
            "featured_articles",
            heading="Featured articles",
            # pylint: disable=E501
            help_text="Select one or more articles to feature on the home page",
        ),
    ]

    subpage_types = [
        "community.CommunityPage",
        "events.EventsIndexPage",
        "facets.FacetIndexPage",
        "forms.ContactFormPage",
        "library.LibraryIndexPage",
        "magazine.MagazineIndexPage",
        "memorials.MemorialIndexPage",
        "store.StoreIndexPage",
        "subscription.SubscriptionIndexPage",
    ]

    max_count = 1

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request)
        # pylint: disable=E501
        context["current_issue"] = (
            MagazineIssue.objects.live().order_by("-publication_date").first()
        )

        return context


class HomePageFeaturedArticle(Orderable):
    home_page = ParentalKey(
        "home.HomePage",
        null=True,
        on_delete=models.CASCADE,
        related_name="featured_articles",
    )

    article = models.ForeignKey(
        MagazineArticle, null=True, on_delete=models.CASCADE, related_name="+"
    )

    panels = [FieldPanel("article")]

    @property
    def title(self):
        return self.article.title

    @property
    def body(self):
        return self.article.body
