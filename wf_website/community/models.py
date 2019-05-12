from django.db import models
from django.http import Http404
from django.shortcuts import render

from wagtail.admin.edit_handlers import (
    FieldPanel,
    InlinePanel,
    MultiFieldPanel,
    PageChooserPanel,
)
from wagtail.core.fields import RichTextField
from wagtail.core.models import Page, Orderable
from wagtail.contrib.routable_page.models import RoutablePageMixin, route
from wagtail.images.edit_handlers import ImageChooserPanel
from wagtail.images.models import Image
from wagtail.search import index

from modelcluster.fields import ParentalKey
from wagtailautocomplete.edit_handlers import AutocompletePanel

from contact.models import Contact


RESOURCE_TYPE_CHOICES = [
    ("online_worship", "Online Worship"),
    ("community_directory", "Community Directory"),
]


class CommunityPage(Page):
    intro = RichTextField(blank=True)

    intro_image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )

    events_intro = RichTextField(blank=True)

    events_image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )

    content_panels = Page.content_panels + [
        MultiFieldPanel(
            [
                FieldPanel("intro", classname="full"),
                ImageChooserPanel('intro_image'),
            ],
            heading="Introduction"
        ),
        MultiFieldPanel(
            [
                FieldPanel("events_intro", classname="full"),
                ImageChooserPanel('events_image'),
            ],
            heading="Upcoming events"
        )
    ]

    max_count = 1

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request)

        context["yearly_meetings"] = Contact.objects.filter(
            contact_type="yearly_meeting").order_by("title")

        return context

    subpage_types = [
        "contact.Contact",
        "community.CommunityResourceIndexPage",
    ]


class CommunityResourceIndexPage(RoutablePageMixin, Page):
    parent_page_types = ["community.CommunityPage"]

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
