from django.db import models
from django.http import Http404
from django.shortcuts import render

from wagtail.admin.edit_handlers import (
    FieldPanel,
    InlinePanel,
    MultiFieldPanel,
    PageChooserPanel,
    StreamFieldPanel,
)
from wagtail.core import blocks
from wagtail.core.fields import RichTextField, StreamField
from wagtail.core.models import Page, Orderable
from wagtail.contrib.routable_page.models import RoutablePageMixin, route
from wagtail.images.edit_handlers import ImageChooserPanel
from wagtail.images.blocks import ImageChooserBlock
from wagtail.images.models import Image
from wagtail.search import index

from modelcluster.fields import ParentalKey
from wagtailautocomplete.edit_handlers import AutocompletePanel

from streams import blocks as wf_blocks


class CommunityPage(Page):
    body = StreamField([
        ("heading", blocks.CharBlock(classname="full title")),
        ("paragraph", blocks.RichTextBlock()),
        ("image", ImageChooserBlock()),
        ("card", wf_blocks.CardBlock()),
        (
            "card_row", blocks.ListBlock(
                wf_blocks.PageCardBlock(label="Page"),
                template="streams/blocks/card_row.html"
            )
        ),
    ], null=True)

    content_panels = Page.content_panels + [
        StreamFieldPanel("body"),
    ]

    max_count = 1

    parent_page_types = ["home.HomePage"]
    subpage_types = [
        "contact.MeetingIndexPage",
        "contact.OrganizationIndexPage",
        "contact.PersonIndexPage",
        "community.CommunityDirectoryIndexPage",
        "community.OnlineWorshipIndexPage",
        "memorials.MemorialIndexPage",
    ]


class OnlineWorship(Page):
    description = RichTextField(blank=True)

    times_of_worship = RichTextField(blank=True)

    website = models.URLField(null=True, blank=True)

    content_panels = Page.content_panels + [
        FieldPanel("description"),
        FieldPanel("times_of_worship"),
        FieldPanel("website"),
    ]

    parent_page_types = [
        "community.OnlineWorshipIndexPage",
    ]
    subpage_types = []

    search_template = "search/online_worship.html"

    search_fields = [
        index.SearchField("description", partial_match=True),
    ]


class OnlineWorshipIndexPage(Page):
    intro = RichTextField(blank=True)

    content_panels = Page.content_panels + [FieldPanel("intro")]

    parent_page_types = ["community.CommunityPage"]
    subpage_types = ["community.OnlineWorship"]

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
    subpage_types = []

    search_template = "search/community_directory.html"

    search_fields = [
        index.SearchField("description", partial_match=True),
    ]


class CommunityDirectoryIndexPage(Page):
    intro = RichTextField(blank=True)

    content_panels = Page.content_panels + [FieldPanel("intro")]

    parent_page_types = ["community.CommunityPage"]
    subpage_types = ["community.CommunityDirectory"]

    max_count = 1

    template = "community/community_directory_index_page.html"
