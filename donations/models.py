from django.db import models

from wagtail.admin.edit_handlers import FieldPanel, StreamFieldPanel
from wagtail.core.blocks import IntegerBlock
from wagtail.core.fields import RichTextField, StreamField
from wagtail.core.models import Page


class DonatePage(Page):
    intro = RichTextField(blank=True)
    suggested_donation_amounts = StreamField([
        ("amount", IntegerBlock())
    ], null=True, blank=True)

    content_panels = Page.content_panels + [
        FieldPanel("intro", classname="full"),
        StreamFieldPanel("suggested_donation_amounts")
    ]

    max_count = 1


class Donation(models.Model):
    amount = models.IntegerField()
