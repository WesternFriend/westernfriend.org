from django.db import models
from django.http import HttpRequest
from django_flatpickr.widgets import DatePickerInput
from modelcluster.contrib.taggit import ClusterTaggableManager  # type: ignore
from modelcluster.fields import ParentalKey  # type: ignore
from taggit.models import TaggedItemBase  # type: ignore
from wagtail.admin.panels import (
    FieldPanel,
    InlinePanel,
    MultiFieldPanel,
    PageChooserPanel,
)
from wagtail.fields import RichTextField, StreamField
from wagtail.models import Orderable, Page
from wagtail.search import index

from common.models import DrupalFields
from core.constants import COMMON_STREAMFIELD_BLOCKS
from facets.models import Audience, Genre, Medium, TimePeriod, Topic
from library.helpers import create_querystring_from_facets, filter_querystring_facets
from pagination.helpers import get_paginated_items


class LibraryItemTag(TaggedItemBase):
    content_object = ParentalKey(
        to="LibraryItem",
        related_name="tagged_items",
        on_delete=models.CASCADE,
    )


class LibraryItem(DrupalFields, Page):  # type: ignore
    publication_date = models.DateField("Publication date", null=True, blank=True)
    publication_date_is_approximate = models.BooleanField(
        default=False,
        help_text="This field indicates when a library item wasn't published on a specific publication date.",  # noqa: E501
    )
    body = StreamField(
        COMMON_STREAMFIELD_BLOCKS,
        null=True,
        blank=True,
        use_json_field=True,
    )
    item_audience = models.ForeignKey(
        "facets.Audience",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    item_genre = models.ForeignKey(
        "facets.Genre",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    item_medium = models.ForeignKey(
        "facets.Medium",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    item_time_period = models.ForeignKey(
        "facets.TimePeriod",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    tags = ClusterTaggableManager(
        through=LibraryItemTag,
        blank=True,
    )

    @classmethod
    def get_queryset(cls):
        related_fields = [
            "authors__author",
            "topics__topic",
            "item_audience",
            "item_genre",
            "item_medium",
            "item_time_period",
            "tags__tag",
        ]
        return (
            super()
            .get_queryset()
            .filter(live=True)
            .prefetch_related(
                *related_fields,
            )
        )

    content_panels = Page.content_panels + [
        InlinePanel(
            "authors",
            heading="Authors",
            help_text="Select one or more authors, who contributed to this article",
        ),
        FieldPanel("body"),
        MultiFieldPanel(
            children=[
                FieldPanel(
                    "publication_date",
                    widget=DatePickerInput(),
                ),
                FieldPanel(
                    "publication_date_is_approximate",
                ),
            ],
            heading="Publication date",
        ),
        MultiFieldPanel(
            children=[
                FieldPanel("item_audience"),
                FieldPanel("item_genre"),
                FieldPanel("item_medium"),
                FieldPanel("item_time_period"),
                InlinePanel(
                    "topics",
                    label="topics",
                ),
                FieldPanel("tags"),
            ],
            heading="Categorization",
        ),
    ]

    search_template = "search/library_item.html"

    search_fields = Page.search_fields + [
        index.SearchField("body"),
        index.RelatedFields(
            "authors",
            [
                index.RelatedFields(
                    "author",
                    [
                        # This will cover the name for all Contact types
                        index.SearchField("title"),
                        index.SearchField("given_name"),  # For Person contacts
                        index.SearchField("family_name"),  # For Person contacts
                    ],
                ),
            ],
        ),
        index.RelatedFields(
            "item_genre",
            [
                index.SearchField("title"),
            ],
        ),
        index.RelatedFields(
            "tags",
            [
                index.SearchField("name"),
            ],
        ),
        index.RelatedFields(
            "topics",
            [
                index.SearchField("topic"),
            ],
        ),
    ]

    parent_page_types = ["LibraryIndexPage"]
    subpage_types: list[str] = []


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
            "author",
            [
                "contact.Person",
                "contact.Meeting",
                "contact.Organization",
            ],
        ),
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
        PageChooserPanel(
            "topic",
        ),
    ]


class LibraryIndexPage(Page):
    intro = RichTextField(blank=True)

    content_panels = Page.content_panels + [FieldPanel("intro")]

    parent_page_types = ["home.HomePage"]
    subpage_types: list[str] = [
        "library.LibraryItem",
        "facets.FacetIndexPage",
    ]

    max_count = 1

    def get_context(
        self,
        request: HttpRequest,
        *args: tuple,
        **kwargs: dict,
    ) -> dict:
        context = super().get_context(request)

        # Prepare a list of authors
        library_item_authors = LibraryItemAuthor.objects.all()
        authors = Page.objects.filter(
            library_items_authored__in=library_item_authors,
        ).distinct()

        # Populate faceted search fields
        context["audiences"] = Audience.objects.all()
        context["genres"] = Genre.objects.all()
        context["mediums"] = Medium.objects.all()
        context["time_periods"] = TimePeriod.objects.all()
        context["topics"] = Topic.objects.all()
        context["authors"] = authors

        query = request.GET.dict()

        facets = filter_querystring_facets(
            query=query,
        )

        # Filter live (not draft) library items using facets from request
        # reverse sort by publication date
        library_items = (
            LibraryItem.objects.live()
            .filter(  # type: ignore
                **facets,
            )
            .order_by("-publication_date")
            .prefetch_related("authors__author")
        )
        page_number = request.GET.get("page", "1")
        items_per_page = 10

        # Provide filtered, paginated library items
        context["paginated_items"] = get_paginated_items(
            items=library_items,
            items_per_page=items_per_page,
            page_number=page_number,
        )

        context["current_querystring"] = create_querystring_from_facets(
            facets=facets,
        )

        return context
