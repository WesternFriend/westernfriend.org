from datetime import date

from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db import models
from django.db.models import Q
from modelcluster.fields import ParentalKey
from timezone_field import TimeZoneField
from wagtail import blocks as wagtail_blocks
from wagtail.admin.panels import FieldPanel, InlinePanel, PageChooserPanel
from wagtail.fields import RichTextField, StreamField
from wagtail.models import Orderable, Page
from wagtail.search import index

from blocks.blocks import FormattedImageChooserStructBlock, HeadingBlock, SpacerBlock


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
            "sponsor", ["contact.Person", "contact.Meeting", "contact.Organization"]
        )
    ]


class Event(Page):
    class EventCategoryChoices(models.TextChoices):
        WESTERN = ("western", "Western")
        OTHER = ("other", "Other")

    teaser = models.TextField(max_length=100, null=True, blank=True)
    body = StreamField(
        [
            ("heading", HeadingBlock()),
            ("rich_text", wagtail_blocks.RichTextBlock()),
            ("image", FormattedImageChooserStructBlock()),
            ("spacer", SpacerBlock()),
        ],
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
        index.SearchField("body", partial_match=True),
    ]

    parent_page_types = ["events.EventsIndexPage"]
    subpage_types = []

    class Meta:
        db_table = "events"
        ordering = ["start_date"]


class EventsIndexPage(Page):
    intro = RichTextField(blank=True)

    content_panels = Page.content_panels + [FieldPanel("intro")]

    parent_page_types = ["home.HomePage"]
    subpage_types = ["events.Event"]

    max_count = 1

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request)
        request_c = request.GET.get("category", None)

        if request_c:
            # Note: using the querystring parameter directly in the filter object
            # seems safe since Django querysets are protected from SQL injection
            # https://docs.djangoproject.com/en/4.1/topics/security/#sql-injection-protection
            # Adding this note to reappraise the security of this code if needed.
            filter_c = request_c
            event_category_title = request_c.capitalize()
        else:
            # Default to Western events
            western_c = Event.EventCategoryChoices.WESTERN
            filter_c = western_c
            event_category_title = western_c.label

        upcoming_events = (
            Event.objects.all()
            .filter(
                Q(start_date__gt=date.today()),
                Q(category=filter_c),
            )
            .order_by("start_date")
        )

        # Show three archive issues per page
        paginator = Paginator(upcoming_events, 3)

        upcoming_events_page = request.GET.get("page")

        try:
            paginated_events = paginator.page(upcoming_events_page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            paginated_events = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            paginated_events = paginator.page(paginator.num_pages)

        context["events"] = paginated_events
        context["event_category_title"] = event_category_title

        return context
