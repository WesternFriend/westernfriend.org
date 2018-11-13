from django.db import models

from wagtail.core.models import Page
from wagtail.core.fields import RichTextField
from wagtail.admin.edit_handlers import FieldPanel

from magazine.models import MagazineIssue


class HomePage(Page):
    body = RichTextField(blank=True)

    content_panels = Page.content_panels + [
        FieldPanel('body', classname="full")
    ]

    subpage_types = [
        'magazine.MagazineIndexPage',
    ]

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request)

        context['current_issue'] = MagazineIssue.objects.live().order_by('-publication_date').first()

        return context