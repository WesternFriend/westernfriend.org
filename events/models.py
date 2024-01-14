from django.utils import timezone
from django.db import models
from django.http import Http404, HttpRequest
from modelcluster.fields import ParentalKey  # type: ignore
from timezone_field import TimeZoneField  # type: ignore
from wagtail.admin.panels import FieldPanel, InlinePanel, PageChooserPanel
from wagtail.fields import RichTextField, StreamField
from wagtail.models import Orderable, Page
from wagtail.search import index

from common.models import DrupalFields
from core.constants import COMMON_STREAMFIELD_BLOCKS
from pagination.helpers import get_paginated_items


class EventSponsor(Orderable):
    event = ParentalKey(
        "events.Event",
        on_delete=models.CASCADE,
        related_name="sponsors",
    )
    sponsor = models.ForeignKey(
        "wagtailcore.Page",
        on_delete=models.CASCADE,
        related_name="events_sponsored",
    )

    panels = [
        PageChooserPanel(
            "sponsor",
            ["contact.Person", "contact.Meeting", "contact.Organization"],
        ),
    ]


class Event(DrupalFields, Page):  # type: ignore
    class EventCategoryChoices(models.TextChoices):
        WESTERN = ("western", "Western")
        OTHER = ("other", "Other")

    teaser = models.TextField(max_length=100, null=True, blank=True)
    body = StreamField(
        COMMON_STREAMFIELD_BLOCKS,
        null=True,
        blank=True,
        use_json_field=True,
    )

    start_date = models.DateTimeField()
    end_date = models.DateTimeField(blank=True, null=True)
    timezone = TimeZoneField(
        default="US/Pacific",
        choices_display="WITH_GMT_OFFSET",
    )

    website = models.URLField(blank=True, null=True, max_length=300)
    is_featured = models.BooleanField(
        default=False,
        help_text="Whether this event should be featured on the home page.",
    )
    category = models.CharField(
        max_length=255,
        choices=EventCategoryChoices.choices,
        default=EventCategoryChoices.WESTERN,
    )
    drupal_node_id = models.IntegerField(null=True, blank=True)

    content_panels = Page.content_panels + [
        FieldPanel("is_featured"),
        FieldPanel("category"),
        InlinePanel(
            "sponsors",
            heading="Sponsors",
            label="Sponsor",
        ),
        FieldPanel("teaser"),
        FieldPanel("body"),
        FieldPanel("start_date"),
        FieldPanel("end_date"),
        FieldPanel("timezone"),
        FieldPanel("website"),
    ]

    context_object_name = "event"

    search_template = "search/event.html"

    search_fields = Page.search_fields + [
        index.SearchField(
            "body",
        ),
    ]

    parent_page_types = ["events.EventsIndexPage"]
    subpage_types: list[str] = []

    class Meta:
        db_table = "events"
        ordering = ["start_date"]


class EventsIndexPage(Page):
    intro = RichTextField(blank=True)

    content_panels = Page.content_panels + [FieldPanel("intro")]

    parent_page_types = ["home.HomePage"]
    subpage_types: list[str] = ["events.Event"]

    max_count = 1

    def get_context(
        self,
        request: HttpRequest,
        *args: tuple,
        **kwargs: dict,
    ) -> dict:
        context = super().get_context(request)
        request_category = request.GET.get("category", None)

        if request_category:
            # Note: using the querystring parameter directly in the filter object
            # seems safe since Django querysets are protected from SQL injection
            # https://docs.djangoproject.com/en/4.1/topics/security/#sql-injection-protection
            # Adding this note to reappraise the security of this code if needed.

            # ensure the category is valid
            filter_category = request_category.lower()
            if filter_category not in Event.EventCategoryChoices.values:
                raise Http404
        else:
            # Default to Western events
            filter_category = Event.EventCategoryChoices.WESTERN

        upcoming_events = (
            Event.objects.live()
            .filter(
                start_date__gt=timezone.now(),
                category=filter_category,
            )
            .order_by("start_date")
        )

        page_number = request.GET.get("page", "1")
        items_per_page = 10

        context["events"] = get_paginated_items(
            items=upcoming_events,
            items_per_page=items_per_page,
            page_number=page_number,
        )

        context["event_category_title"] = filter_category.capitalize()

        return context
