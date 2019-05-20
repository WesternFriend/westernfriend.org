from enum import Enum

from django.db import models
from django.utils.text import slugify
from django_extensions.db.fields import AutoSlugField


from modelcluster.models import ClusterableModel
from wagtail.admin.edit_handlers import FieldPanel
from wagtail.core.models import Page
from wagtail.core.fields import RichTextField
from wagtail.search import index

MEETING_TYPE_CHOICES = (
    ("monthly_meeting", "Monthly Meeting"),
    ("quarterly_meeting", "Quarterly Meeting"),
    ("worship_group", "Worship Group"),
    ("yearly_meeting", "Yearly Meeting"),
)


class Person(Page):
    given_name = models.CharField(
        max_length=255,
        default="",
        help_text="Enter the given name for a person.",
    )

    family_name = models.CharField(max_length=255, blank=True, default="")

    content_panels = [
        FieldPanel("given_name"),
        FieldPanel("family_name"),
    ]

    template = "contact/contact.html"

    class Meta:
        db_table = "person"
        ordering = ["title"]

    def save(self, *args, **kwargs):
        full_name = f"{self.given_name} {self.family_name}"
        self.title = full_name.strip()

        super(Person, self).save(*args, **kwargs)

    search_fields = [
        index.SearchField("given_name", partial_match=True),
        index.SearchField("family_name", partial_match=True),
    ]

    parent_page_types = ["community.CommunityPage"]
    subpage_types = []


class Meeting(Page):
    meeting_type = models.CharField(
        max_length=255, choices=MEETING_TYPE_CHOICES)

    description = models.CharField(max_length=255, blank=True, null=True)

    website = models.URLField(null=True, blank=True)

    content_panels = Page.content_panels + [
        FieldPanel("description"),
        FieldPanel("website"),
        FieldPanel("meeting_type"),
    ]

    parent_page_types = ["community.CommunityPage", "Meeting"]
    subpage_types = ["Meeting"]

    template = "contact/contact.html"

    class Meta:
        db_table = "meeting"
        ordering = ["title"]

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request)

        context["quarterly_meetings"] = Meeting.objects.child_of(
            self).filter(meeting_type="quarterly_meeting")

        context["monthly_meetings"] = Meeting.objects.descendant_of(
            self).filter(meeting_type="monthly_meeting")

        context["worship_groups"] = Meeting.objects.descendant_of(
            self).filter(meeting_type="worship_group")

        return context


class Organization(Page):
    description = models.CharField(max_length=255, blank=True, null=True)

    website = models.URLField(null=True, blank=True)

    content_panels = Page.content_panels + [
        FieldPanel("description"),
        FieldPanel("website"),
    ]

    parent_page_types = ["community.CommunityPage"]
    subpage_types = []

    template = "contact/contact.html"

    class Meta:
        db_table = "organization"
        ordering = ["title"]


class Contact(Page):
    # TODO: determine how to delete this model
    class Meta:
        db_table = "contact"
