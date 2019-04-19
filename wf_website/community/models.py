from django.db import models

from wagtail.admin.edit_handlers import FieldPanel, InlinePanel, PageChooserPanel
from wagtail.core.fields import RichTextField
from wagtail.core.models import Page, Orderable

from modelcluster.fields import ParentalKey
from wagtailautocomplete.edit_handlers import AutocompletePanel


class CommunityPage(Page):
    intro = RichTextField(blank=True)

    content_panels = Page.content_panels + [
        FieldPanel("intro", classname="full"),
        InlinePanel(
            "yearly_meetings",
            heading="Yearly Meetings",
            # pylint: disable=E501
            help_text="Select yearly meetings for the community directory",
        ),
    ]

    subpage_types = ["YearlyMeetingPage"]

    max_count = 1

    # def get_context(self, request, *args, **kwargs):
    #     context = super().get_context(request)
    #     # pylint: disable=E501
    #     # TODO: get upcoming events
    #     context['upcoming_events'] = MagazineIssue.objects.live().order_by('-publication_date').first()

    #     return context


class YearlyMeetingPage(Page):
    intro = RichTextField(blank=True)

    yearly_meeting = models.ForeignKey(
        "contact.Contact",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    content_panels = Page.content_panels + [
        FieldPanel("intro", classname="full"),
        AutocompletePanel("yearly_meeting", page_type="contact.Contact"),
    ]

    subpage_types = []


class CommunityPageYearlyMeeting(Orderable):
    community_page_instance = ParentalKey(
        "community.CommunityPage",
        null=True,
        on_delete=models.CASCADE,
        related_name="yearly_meetings",
    )

    yearly_meeting = models.ForeignKey(
        YearlyMeetingPage, null=True, on_delete=models.CASCADE, related_name="+"
    )

    panels = [FieldPanel("yearly_meeting")]

    @property
    def title(self):
        return self.yearly_meeting.title

    @property
    def intro(self):
        return self.yearly_meeting.intro
