from django.db import models

from wagtail.admin.edit_handlers import FieldPanel
from wagtail.core.models import Page
from wagtail.core.fields import RichTextField
from wagtail.images.edit_handlers import ImageChooserPanel
from wagtail.search import index


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

    content_panels = Page.content_panels + [
        ImageChooserPanel('cover_image'),
    ]

    subpage_types = [
        'MagazineArticle',
    ]


class MagazineArticle(Page):
    body = RichTextField(blank=True)

    search_fields = Page.search_fields + [
        index.SearchField('body'),
    ]

    content_panels = Page.content_panels + [
        FieldPanel('body', classname="full")
    ]

    subpage_types = []
