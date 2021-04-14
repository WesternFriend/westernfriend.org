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

from modelcluster.contrib.taggit import ClusterTaggableManager
from modelcluster.fields import ParentalKey
from taggit.models import TaggedItemBase

from facets.models import (
    Audience,
    Genre,
    Medium,
    TimePeriod,
    Topic,
)

from flatpickr import DatePickerInput


class LibraryItemTag(TaggedItemBase):
    content_object = ParentalKey(
        to="LibraryItem", related_name="tagged_items", on_delete=models.CASCADE
    )


class LibraryItem(Page):
    publication_date = models.DateField("Publication date", null=True, blank=True)
    description = RichTextField(null=True, blank=True)
    body = StreamField(
        [
            ("paragraph", blocks.RichTextBlock()),
            ("image", ImageChooserBlock()),
            ("document", DocumentChooserBlock()),
            ("embed", EmbedBlock()),
            ("url", blocks.URLBlock()),
            ("quote", blocks.BlockQuoteBlock()),
        ],
        null=True,
        blank=True,
    )
    item_audience = models.ForeignKey(
        "facets.Audience", on_delete=models.SET_NULL, null=True, blank=True
    )
    item_genre = models.ForeignKey(
        "facets.Genre", on_delete=models.SET_NULL, null=True, blank=True
    )
    item_medium = models.ForeignKey(
        "facets.Medium", on_delete=models.SET_NULL, null=True, blank=True
    )
    item_time_period = models.ForeignKey(
        "facets.TimePeriod", on_delete=models.SET_NULL, null=True, blank=True
    )
    tags = ClusterTaggableManager(through=LibraryItemTag, blank=True)
    drupal_node_id = models.IntegerField(null=True, blank=True)

    content_panels = Page.content_panels + [
        FieldPanel("description"),
        InlinePanel(
            "authors",
            heading="Authors",
            help_text="Select one or more authors, who contributed to this article",
        ),
        FieldPanel("publication_date", widget=DatePickerInput()),
        StreamFieldPanel("body"),
        MultiFieldPanel(
            children=[
                FieldPanel("item_audience"),
                FieldPanel("item_genre"),
                FieldPanel("item_medium"),
                FieldPanel("item_time_period"),
                InlinePanel("topics", label="topics"),
                FieldPanel("tags"),
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
        "wagtailcore.Page",
        null=True,
        on_delete=models.CASCADE,
        related_name="library_items_authored",
    )

    panels = [
        PageChooserPanel(
            "author", ["contact.Person", "contact.Meeting", "contact.Organization", ]
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
        related_name="related_library_items",
    )

    panels = [
        PageChooserPanel("topic",),
    ]


class LibraryIndexPage(Page):
    intro = RichTextField(blank=True)

    content_panels = Page.content_panels + [FieldPanel("intro")]

    parent_page_types = ["home.HomePage"]
    subpage_types = [
        "library.LibraryItem",
        "facets.FacetIndexPage",
    ]

    max_count = 1

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request)

        # Prepare a list of authors
        library_item_authors = LibraryItemAuthor.objects.all()
        authors = Page.objects.filter(
            library_items_authored__in=library_item_authors
        ).distinct()

        # Populate faceted search fields
        context["audiences"] = Audience.objects.all()
        context["genres"] = Genre.objects.all()
        context["mediums"] = Medium.objects.all()
        context["time_periods"] = TimePeriod.objects.all()
        context["topics"] = Topic.objects.all()
        context["authors"] = authors

        query = request.GET.dict()

        # Filter out any facet that isn't a model field
        allowed_keys = [
            "authors__author__title",
            "item_audience__title",
            "item_genre__title",
            "item_medium__title",
            "item_time_period__title",
            "item_topic__title",
        ]
        facets = {key: query[key] for key in query if key in allowed_keys}

        # Filter library items using facets from GET request
        library_items = LibraryItem.objects.filter(**facets)

        # Provide filtered library items
        context["library_items"] = library_items

        return context
