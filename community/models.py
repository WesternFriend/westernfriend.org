from django.db import models
from django.http import HttpRequest
from wagtail import blocks as wagtail_blocks
from wagtail.admin.panels import FieldPanel, PageChooserPanel
from wagtail.fields import RichTextField, StreamField
from wagtail.images.blocks import ImageChooserBlock
from wagtail.models import Page
from wagtail.search import index

from timezone_field import TimeZoneField  # type: ignore

from blocks import blocks as wf_blocks
from common.models import DrupalFields


class CommunityPage(Page):
    body = StreamField(
        [
            ("heading", wf_blocks.HeadingBlock()),
            ("rich_text", wagtail_blocks.RichTextBlock()),
            ("image", ImageChooserBlock()),
            ("card", wf_blocks.CardBlock()),
            (
                "card_row",
                wagtail_blocks.ListBlock(
                    wf_blocks.PageCardBlock(label="Page"),
                    template="blocks/blocks/card_row.html",
                ),
            ),
            ("spacer", wf_blocks.SpacerBlock()),
        ],
        null=True,
        use_json_field=True,
    )

    content_panels = Page.content_panels + [
        FieldPanel("body"),
    ]

    max_count = 1

    parent_page_types = ["home.HomePage"]
    subpage_types: list[str] = [
        "contact.MeetingIndexPage",
        "contact.OrganizationIndexPage",
        "contact.PersonIndexPage",
        "community.CommunityDirectoryIndexPage",
        "community.OnlineWorshipIndexPage",
        "memorials.MemorialIndexPage",
    ]


class OnlineWorship(DrupalFields, Page):
    class OnlineWorshipDayChoices(models.TextChoices):
        SUNDAY = "Sunday", "Sunday"
        MONDAY = "Monday", "Monday"
        TUESDAY = "Tuesday", "Tuesday"
        WEDNESDAY = "Wednesday", "Wednesday"
        THURSDAY = "Thursday", "Thursday"
        FRIDAY = "Friday", "Friday"
        SATURDAY = "Saturday", "Saturday"

    description = RichTextField(blank=True)

    hosted_by = models.ForeignKey(
        "wagtailcore.Page",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="online_worship",
    )
    # TODO: Define a custom, orderable model for this
    # to allow for multiple times of worship.
    times_of_worship = RichTextField(blank=True)
    online_worship_day = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        choices=OnlineWorshipDayChoices.choices,
    )
    online_worship_time = models.TimeField(null=True, blank=True)
    online_worship_timezone = TimeZoneField(
        null=True,
        blank=True,
    )

    website = models.URLField(null=True, blank=True)

    drupal_node_id = models.IntegerField(null=True, blank=True)
    drupal_body_migrated = models.TextField(null=True, blank=True)
    drupal_url_path = models.CharField(max_length=255, null=True, blank=True)

    content_panels = Page.content_panels + [
        FieldPanel("description"),
        PageChooserPanel("hosted_by", ["contact.Meeting", "contact.Organization"]),
        FieldPanel("times_of_worship"),
        FieldPanel("website"),
    ]

    parent_page_types = [
        "community.OnlineWorshipIndexPage",
    ]
    subpage_types: list[str] = []

    search_template = "search/online_worship.html"

    search_fields = Page.search_fields + [
        index.SearchField(
            "description",
        ),
        index.RelatedFields(
            "hosted_by",
            [
                index.SearchField("title"),
            ],
        ),
    ]


class OnlineWorshipIndexPage(Page):
    intro = RichTextField(blank=True)

    content_panels = Page.content_panels + [FieldPanel("intro")]

    parent_page_types = ["community.CommunityPage"]
    subpage_types: list[str] = ["community.OnlineWorship"]

    max_count = 1

    template = "community/online_worship_index_page.html"

    def get_context(
        self,
        request: HttpRequest,
        *args: tuple,
        **kwargs: dict,
    ) -> dict:
        context = super().get_context(request, *args, **kwargs)

        # Get all live OnlineWorship objects sorted by title
        online_worship_meetings = OnlineWorship.objects.live().order_by(
            "title",
        )

        context["online_worship_meetings"] = online_worship_meetings

        return context


class CommunityDirectory(Page):
    description = RichTextField(blank=True)

    website = models.URLField(null=True, blank=True)

    content_panels = Page.content_panels + [
        FieldPanel("description"),
        FieldPanel("website"),
    ]

    parent_page_types = [
        "community.CommunityDirectoryIndexPage",
    ]
    subpage_types: list[str] = []

    search_template = "search/community_directory.html"

    search_fields = Page.search_fields + [
        index.SearchField(
            "description",
        ),
    ]

    class Meta:
        verbose_name_plural = "community directories"


class CommunityDirectoryIndexPage(Page):
    intro = RichTextField(blank=True)

    content_panels = Page.content_panels + [FieldPanel("intro")]

    parent_page_types = ["community.CommunityPage"]
    subpage_types: list[str] = ["community.CommunityDirectory"]

    max_count = 1

    template = "community/community_directory_index_page.html"
