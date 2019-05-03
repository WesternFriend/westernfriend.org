from django.db import models

from wagtail.admin.edit_handlers import FieldPanel, InlinePanel, PageChooserPanel
from wagtail.core.fields import RichTextField
from wagtail.core.models import Page, Orderable

from modelcluster.fields import ParentalKey
from wagtailautocomplete.edit_handlers import AutocompletePanel

from contact.models import Contact


class CommunityPage(Page):
    intro = RichTextField(blank=True)

    content_panels = Page.content_panels + [
        FieldPanel("intro", classname="full"),
    ]

    subpage_types = []

    max_count = 1

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request)
        # pylint: disable=E501
        # TODO: get upcoming events
        #context['upcoming_events'] = MagazineIssue.objects.live().order_by('-publication_date').first()
        context["yearly_meetings"] = Contact.objects.filter(
            contact_type="yearly_meeting")

        return context
