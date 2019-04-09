from django.db import models

from wagtail.admin.edit_handlers import FieldPanel, StreamFieldPanel
from wagtail.core.models import Page
from wagtail.core.fields import RichTextField, StreamField
from wagtail.core import blocks
from wagtail.documents.blocks import DocumentChooserBlock
from wagtail.embeds.blocks import EmbedBlock
from wagtail.images.blocks import ImageChooserBlock

from modelcluster.fields import ParentalManyToManyField


class LibraryItem(Page):
    authored_by = ParentalManyToManyField("contact.Contact", related_name="media_items")
    publication_date = models.DateField("Publication date")
    body = StreamField(
        [
            ("paragraph", blocks.RichTextBlock()),
            ("image", ImageChooserBlock()),
            ("document", DocumentChooserBlock()),
            ("embed", EmbedBlock()),
            ("url", blocks.URLBlock()),
            ("quote", blocks.BlockQuoteBlock()),
        ]
    )

    content_panels = Page.content_panels + [
        FieldPanel("authored_by"),
        FieldPanel("publication_date"),
        StreamFieldPanel("body"),
    ]

    parent_page_types = ["LibraryIndexPage"]
    subpage_types = []


class LibraryIndexPage(Page):
    intro = RichTextField(blank=True)

    content_panels = Page.content_panels + [FieldPanel("intro")]

    # parent_page_types = ["home.HomePage"]
    subpage_types = ["LibraryItem"]

    max_count = 1
