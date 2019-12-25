from django.db import models

from wagtail.admin.edit_handlers import FieldPanel, PageChooserPanel
from wagtail.core.fields import RichTextField
from wagtail.core.models import Page
from wagtail.search import index

from flatpickr import DatePickerInput


class Memorial(Page):
    given_name = models.CharField(
        max_length=255,
        default="",
        help_text="Enter the given name for a person.",
    )
    family_name = models.CharField(max_length=255, blank=True, default="")
    date_of_birth = models.DateField()
    date_of_death = models.DateField()
    dates_are_approximate = models.BooleanField()
    memorial_minute = RichTextField(blank=True)
    memorial_meeting = models.ForeignKey(
        to="contact.Meeting",
        on_delete=models.PROTECT,
        related_name="memorial_minutes"
    )

    def full_name(self):
        return f"{ self.given_name } { self.family_name }"

    content_panels = [
        FieldPanel("given_name"),
        FieldPanel("family_name"),
        FieldPanel("date_of_birth", widget=DatePickerInput()),
        FieldPanel("date_of_death", widget=DatePickerInput()),
        FieldPanel("dates_are_approximate"),
        FieldPanel("memorial_minute"),
        PageChooserPanel("memorial_meeting"),
    ]

    parent_page_types = [
        "MemorialIndexPage",
    ]

    def save(self, *args, **kwargs):
        self.title = self.full_name()

        super(Memorial, self).save(*args, **kwargs)

    search_fields = [
        index.SearchField("given_name", partial_match=True),
        index.SearchField("family_name", partial_match=True),
    ]


class MemorialIndexPage(Page):
    intro = RichTextField(blank=True)

    max_count = 1

    content_panels = Page.content_panels + [
        FieldPanel("intro")
    ]

    subpage_types = [
        Memorial,
    ]
