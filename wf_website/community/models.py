from django.db import models

from wagtail.admin.edit_handlers import (
    FieldPanel,
    InlinePanel,
    MultiFieldPanel,
    PageChooserPanel,
)
from wagtail.core.fields import RichTextField
from wagtail.core.models import Page, Orderable
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

    subpage_types = []

    max_count = 1

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request)

        context["yearly_meetings"] = Contact.objects.filter(
            contact_type="yearly_meeting").order_by("title")

        return context

    subpage_types = [
        "contact.Contact",
        "community.CommunityResource",
    ]


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

    parent_page_types = ["community.CommunityPage"]

    search_fields = [
        index.SearchField("description", partial_match=True),
    ]
