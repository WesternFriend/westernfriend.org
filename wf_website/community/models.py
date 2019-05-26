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

RESOURCE_TYPE_CHOICES = [
    ("online_worship", "Online Worship"),
    ("community_directory", "Community Directory"),
]


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

    community_resources_index_page = models.ForeignKey(
        'wagtailcore.Page',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
    )

    quaker_organizations_intro = RichTextField(blank=True)

    online_worship_intro = RichTextField(blank=True)

    community_directories_intro = RichTextField(blank=True)

    content_panels = Page.content_panels + [
        StreamFieldPanel("body"),
        MultiFieldPanel(
            [
                PageChooserPanel(
                    'community_resources_index_page',
                    'community.CommunityResourceIndexPage'),
                FieldPanel("quaker_organizations_intro"),
                FieldPanel("online_worship_intro"),
                FieldPanel("community_directories_intro"),
            ],
            heading="Community resources"
        )
    ]

    max_count = 1

    subpage_types = [
        "contact.Person",
        "contact.Meeting",
        "contact.Organization",
        "contact.OrganizationIndexPage",
        "community.OnlineWorshipIndexPage",
        "community.CommunityResourceIndexPage",
    ]


class CommunityResourceIndexPage(RoutablePageMixin, Page):
    parent_page_types = ["community.CommunityPage"]

    max_count = 1

    @route(r'^([\w-]+)/$')
    def events_for_year(self, request, resource_type=None):
        """
        View function for the community resources page

        Takes a "resource_type" argument for queryset
        """

        # format to snake case, for query
        resource_type = resource_type.replace("-", "_")

        try:
            resources = CommunityResource.objects.filter(
                resource_type=resource_type)
        except:
            raise Http404("Could not find resources")

        return render(
            request,
            "community/community_resource_index_page.html",
            {"resources": resources}
        )


class CommunityResource(Page):
    description = RichTextField(blank=True)

    website = models.URLField(null=True, blank=True)

    resource_type = models.CharField(
        max_length=255, choices=RESOURCE_TYPE_CHOICES)

    content_panels = Page.content_panels + [
        FieldPanel("description"),
        FieldPanel("website"),
        FieldPanel("resource_type"),
    ]

    parent_page_types = ["community.CommunityResourceIndexPage"]
    subpage_types = []

    search_fields = [
        index.SearchField("description", partial_match=True),
    ]


class OnlineWorship(Page):
    description = RichTextField(blank=True)

    times_of_worship = RichTextField(blank=True)

    website = models.URLField(null=True, blank=True)

    content_panels = Page.content_panels + [
        FieldPanel("description"),
        FieldPanel("description"),
        FieldPanel("website"),
    ]

    parent_page_types = [
        "community.OnlineWorshipIndexPage",
    ]
    subpage_types = []

    search_fields = [
        index.SearchField("description", partial_match=True),
    ]


class OnlineWorshipIndexPage(Page):
    intro = RichTextField(blank=True)

    content_panels = Page.content_panels + [FieldPanel("intro")]

    subpage_types = ["community.OnlineWorship"]
    
    max_count = 1

    template = "community/online_worship_index_page.html"
