from datetime import timedelta

from django.db import models

from modelcluster.fields import ParentalKey

from wagtail.admin.edit_handlers import FieldPanel, InlinePanel, PageChooserPanel
from wagtail.core.models import Page, Orderable
from wagtail.core.fields import RichTextField
from wagtail.images.edit_handlers import ImageChooserPanel
from wagtail.search import index
from wagtail.snippets.edit_handlers import SnippetChooserPanel
from wagtail.snippets.models import register_snippet


class MagazineIndexPage(Page):
    intro = RichTextField(blank=True)

    content_panels = Page.content_panels + [
        FieldPanel('intro')
    ]

    subpage_types = [
        'MagazineIssue',
    ]


class MagazineIssue(Page):
    cover_image = models.ForeignKey(
        'wagtailimages.Image',
        on_delete=models.SET_NULL,
        null=True,
        related_name='+',
    )
    publication_date = models.DateField(
        null=True,
        help_text="Please select the first day of the publication month",
    )

    @property
    def publication_end_date(self):
        if self.publication_date:
            # TODO: try to find a cleaner way to add a month to the publication date
            # I.e. the 'add a month' approach may be flawed altogether.
            return self.publication_date + timedelta(days=+31)

    content_panels = Page.content_panels + [
        FieldPanel('publication_date'),
        ImageChooserPanel('cover_image'),
        InlinePanel(
            'featured_articles',
            heading="Featured articles",
            help_text="Select one or more featured articles, from this issue",
        ),
    ]

    subpage_types = [
        'MagazineArticle',
    ]

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request)

        context['articles_by_department'] = MagazineArticle.objects.child_of(self).live().order_by('department__name')

        return context


class MagazineArticle(Page):
    body = RichTextField(blank=True)
    department = models.ForeignKey(
        'MagazineDepartment',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
    )

    search_fields = Page.search_fields + [
        index.SearchField('body'),
    ]

    content_panels = Page.content_panels + [
        FieldPanel('body', classname="full"),
        SnippetChooserPanel('department'),
    ]

    subpage_types = []


@register_snippet
class MagazineDepartment(models.Model):
    name = models.CharField(max_length=200)

    panels = [
        FieldPanel('name')
    ]

    def __str__(self):
        return self.name


class MagazineIssueFeaturedArticle(Orderable):
    issue = ParentalKey(
        'magazine.MagazineIssue',
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
        PageChooserPanel('article')
    ]