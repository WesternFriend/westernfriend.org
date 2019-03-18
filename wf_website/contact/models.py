from django.db import models
from wagtail.core.models import Page
from wagtail.core.fields import RichTextField
from wagtail.admin.edit_handlers import FieldPanel


class ContactIndexPage(Page):
    intro = RichTextField(blank=True)

    content_panels = Page.content_panels + [FieldPanel("intro")]

    subpage_types = ["Contact"]

    max_count = 1


class Contact(Page):
    class Meta:
        db_table = "contact"

    parent_page_types = ["ContactIndexPage"]
    subpage_types = []
