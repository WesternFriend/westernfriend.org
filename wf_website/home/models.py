from django.db import models
from modelcluster.fields import ParentalKey

from wagtail.core.models import Page, Orderable
from wagtail.core.fields import RichTextField
from wagtail.admin.edit_handlers import FieldPanel, InlinePanel

from magazine.models import MagazineIssue, MagazineArticle


class HomePage(Page):
    intro = RichTextField(blank=True)

    content_panels = Page.content_panels + [
        FieldPanel('intro', classname="full"),
        InlinePanel(
            'featured_articles',
            heading="Featured articles",
            help_text="Select one or more articles to feature on the home page",
        )
    ]

    subpage_types = [
        'magazine.MagazineIndexPage',
        'magazine.MagazineTagIndexPage',
    ]

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request)

        context['current_issue'] = MagazineIssue.objects.live().order_by('-publication_date').first()

        return context


class HomePageFeaturedArticle(Orderable):
    home_page = ParentalKey(
        'home.HomePage',
        null=True,
        on_delete=models.CASCADE,
        related_name='featured_articles',
    )

    article = models.ForeignKey(
        MagazineArticle,
        null=True,
        on_delete=models.CASCADE,
        related_name='+',
    )

    panels = [
        FieldPanel('article')
    ]

    @property
    def title(self):
        return self.article.title

    @property
    def body(self):
        return self.article.body