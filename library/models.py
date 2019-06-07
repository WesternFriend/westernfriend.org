from django.db import models

from wagtail.admin.edit_handlers import (
    FieldPanel,
    InlinePanel,
    MultiFieldPanel,
    PageChooserPanel,
    StreamFieldPanel,
)
from wagtail.core.models import Orderable, Page
from wagtail.core.fields import RichTextField, StreamField
from wagtail.core import blocks
from wagtail.documents.blocks import DocumentChooserBlock
from wagtail.embeds.blocks import EmbedBlock
from wagtail.images.blocks import ImageChooserBlock

from modelcluster.fields import (
    ParentalKey,
)

class LibraryItem(Page):
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
    item_audience = models.ForeignKey(
        "facets.Audience",
        on_delete=models.SET_NULL,
        null=True
    )
    item_genre = models.ForeignKey(
        "facets.Genre",
        on_delete=models.SET_NULL,
        null=True
    )
    item_medium = models.ForeignKey(
        "facets.Medium",
        on_delete=models.SET_NULL,
        null=True
    )
    item_time_period = models.ForeignKey(
        "facets.TimePeriod",
        on_delete=models.SET_NULL,
        null=True
    )

    content_panels = Page.content_panels + [
        InlinePanel(
            "authors",
            heading="Authors",
            help_text="Select one or more authors, who contributed to this article",
        ),
        FieldPanel("publication_date"),
        StreamFieldPanel("body"),
        MultiFieldPanel(	
            children=[	
                FieldPanel("item_audience"),	
                FieldPanel("item_genre"),	
                FieldPanel("item_medium"),	
                FieldPanel("item_time_period"),
                InlinePanel(
                    "topics",
                    label="topics"
                )
            ],	
            heading="Categorization",	
        ),
    ]

    parent_page_types = ["LibraryIndexPage"]
    subpage_types = []


class LibraryItemAuthor(Orderable):
    library_item = ParentalKey(
        "library.LibraryItem",
        null=True,
        on_delete=models.CASCADE,
        related_name="authors",
    )
    author = models.ForeignKey(
        "wagtailcore.Page", null=True, on_delete=models.CASCADE, related_name="library_items_authored"
    )

    panels = [
        PageChooserPanel(
            "author",
            [
                "contact.Person",
                "contact.Meeting",
                "contact.Organization",
            ]
        )
    ]


class LibraryItemTopic(Orderable):
    library_item = ParentalKey(
        "library.LibraryItem",
        null=True,
        on_delete=models.CASCADE,
        related_name="topics",
    )
    topic = models.ForeignKey(
        "facets.Topic",
        null=True,
        on_delete=models.CASCADE,
        related_name="related_library_items"
    )

    panels = [
        PageChooserPanel(
            "topic",
        ),
    ]


class LibraryIndexPage(Page):
    intro = RichTextField(blank=True)

    content_panels = Page.content_panels + [FieldPanel("intro")]

    # parent_page_types = ["home.HomePage"]
    subpage_types = ["LibraryItem"]

    max_count = 1
