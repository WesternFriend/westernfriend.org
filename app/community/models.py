from django.db import models
from wagtail import blocks as wagtail_blocks
from wagtail.admin.panels import FieldPanel, PageChooserPanel
from wagtail.fields import RichTextField, StreamField
from wagtail.images.blocks import ImageChooserBlock
from wagtail.models import Page
from wagtail.search import index

from blocks import blocks as wf_blocks


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


class OnlineWorship(Page):
    description = RichTextField(blank=True)

    hosted_by = models.ForeignKey(
        "wagtailcore.Page",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="online_worship",
    )

    times_of_worship = RichTextField(blank=True)

    website = models.URLField(null=True, blank=True)

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
        index.SearchField("description", partial_match=True),
    ]


class OnlineWorshipIndexPage(Page):
    intro = RichTextField(blank=True)

    content_panels = Page.content_panels + [FieldPanel("intro")]

    parent_page_types = ["community.CommunityPage"]
    subpage_types: list[str] = ["community.OnlineWorship"]

    max_count = 1

    template = "community/online_worship_index_page.html"


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
        index.SearchField("description", partial_match=True),
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
