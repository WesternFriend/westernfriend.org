from django.db import models

from wagtail.admin.edit_handlers import FieldPanel
from wagtail.core.fields import RichTextField
from wagtail.core.models import Page

# Create your models here.


class Event(Page):
    description = RichTextField(blank=True)

    date = models.DateTimeField()

    website = models.URLField(blank=True, null=True)

    content_panels = Page.content_panels + [
        FieldPanel("description"),
        FieldPanel("date"),
        FieldPanel("website")
    ]

    class Meta:
        db_table = "events"
