from wagtail.admin.edit_handlers import FieldPanel, InlinePanel
from wagtail.core.fields import RichTextField
from wagtail.core.models import Page, Orderable


class CommunityPage(Page):
    intro = RichTextField(blank=True)

    content_panels = Page.content_panels + [
        FieldPanel("intro", classname="full"),
        # InlinePanel(
        #     "yearly_meetings",
        #     heading="Yearly Meetings",
        #     # pylint: disable=E501
        #     help_text="Select yearly meetings for the community directory",
        # ),
    ]

    subpage_types = []

    max_count = 1

    # def get_context(self, request, *args, **kwargs):
    #     context = super().get_context(request)
    #     # pylint: disable=E501
    #     # TODO: get upcoming events
    #     context['upcoming_events'] = MagazineIssue.objects.live().order_by('-publication_date').first()

    #     return context
