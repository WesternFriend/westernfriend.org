from django.db import models
from django.utils.text import slugify
from django_extensions.db.fields import AutoSlugField

from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel
from wagtail.admin.edit_handlers import (
    FieldPanel,
    InlinePanel,
    MultiFieldPanel,
    PageChooserPanel,
    StreamFieldPanel,
)
from wagtail.core import blocks
from wagtail.core.models import Orderable, Page
from wagtail.core.fields import RichTextField, StreamField
from wagtail.search import index

from addresses.models import Address
from streams.blocks import OrganizationsBlock

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
        null=True,
        blank=True,
    )

    family_name = models.CharField(max_length=255, blank=True, default="")
    drupal_full_name = models.CharField(
        max_length=255, db_index=True, null=True, blank=True, unique=True
    )
    drupal_term_id = models.IntegerField(null=True, blank=True)
    civicrm_id = models.IntegerField(null=True, blank=True)

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

    parent_page_types = ["contact.PersonIndexPage"]
    subpage_types = []


class PersonIndexPage(Page):
    max_count = 1

    parent_page_types = ["community.CommunityPage"]
    subpage_types = ["contact.Person"]

    template = "contact/person_index_page.html"


class MeetingPresidingClerk(Orderable):
    """Presiding clerk of Quaker meeting."""
    meeting = ParentalKey("contact.Meeting", related_name="presiding_clerks")
    person = models.ForeignKey(
        "contact.Person",
        null=True,
        blank=False,
        on_delete=models.SET_NULL,
        related_name="clerk_of",
    )

    panels = [
        PageChooserPanel("person", "contact.Person"),
    ]


class Meeting(Page):
    meeting_type = models.CharField(
        max_length=255, choices=MEETING_TYPE_CHOICES, null=True, blank=True,
    )

    description = RichTextField(blank=True, null=True)
    website = models.URLField(null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    phone = models.CharField(max_length=64, null=True, blank=True)
    civicrm_id = models.IntegerField(null=True, blank=True)
    drupal_full_name = models.CharField(
        max_length=255, db_index=True, null=True, blank=True, unique=True
    )
    drupal_term_id = models.IntegerField(null=True, blank=True)

    content_panels = Page.content_panels + [
        FieldPanel("description"),
        FieldPanel("website"),
        FieldPanel("email"),
        FieldPanel("phone"),
        FieldPanel("meeting_type"),
        InlinePanel("worship_times", label="Worship times"),
        InlinePanel("addresses", label="Address"),
        MultiFieldPanel(
            [InlinePanel("presiding_clerks", label="Presiding clerk")],
            heading="Presiding clerk(s)"
        )
    ]

    parent_page_types = ["contact.MeetingIndexPage", "Meeting"]
    subpage_types = ["Meeting"]

    template = "contact/contact.html"

    search_template = "search/meeting.html"

    search_fields = [
        index.SearchField("description", partial_match=True),
    ]

    class Meta:
        db_table = "meeting"
        ordering = ["title"]

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request)

        context["quarterly_meetings"] = Meeting.objects.child_of(self).filter(
            meeting_type="quarterly_meeting"
        ).order_by('title')

        context["monthly_meetings"] = Meeting.objects.descendant_of(self).filter(
            meeting_type="monthly_meeting"
        ).order_by('title')

        context["worship_groups"] = Meeting.objects.descendant_of(self).filter(
            meeting_type="worship_group"
        ).order_by('title')

        return context


class MeetingAddress(Orderable, Address):
    page = ParentalKey(
        "contact.Meeting", on_delete=models.CASCADE, related_name="addresses"
    )


class WorshipTypeChoices(models.TextChoices):
    FIRST_DAY_WORSHIP = "first_day_worship", "First day worship"
    FIRST_DAY_WORSHIP_2ND = "first_day_worship_2nd", "First day worship, 2nd"
    BUSINESS_MEETING = "business_meeting", "Business meeting"
    OTHER_REGULAR_MEETING = "other_regular_meeting", "Other regular meeting"


class MeetingWorshipTime(Orderable):
    meeting = ParentalKey("contact.Meeting", on_delete=models.CASCADE, related_name="worship_times")
    worship_type = models.CharField(
        max_length=255, choices=WorshipTypeChoices.choices, null=True, blank=True,
    )
    worship_time = models.CharField(max_length=255)


class MeetingIndexPage(Page):
    max_count = 1

    parent_page_types = ["community.CommunityPage"]
    subpage_types = ["contact.Meeting"]

    template = "contact/meeting_index_page.html"


class Organization(Page):
    description = models.CharField(max_length=255, blank=True, null=True)

    website = models.URLField(null=True, blank=True)
    civicrm_id = models.IntegerField(null=True, blank=True)
    drupal_full_name = models.CharField(
        max_length=255, db_index=True, null=True, blank=True, unique=True
    )
    drupal_term_id = models.IntegerField(null=True, blank=True)

    content_panels = Page.content_panels + [
        FieldPanel("description"),
        FieldPanel("website"),
    ]

    parent_page_types = ["contact.OrganizationIndexPage"]
    subpage_types = []

    template = "contact/contact.html"

    search_template = "search/organization.html"

    search_fields = [
        index.SearchField("description", partial_match=True),
    ]

    class Meta:
        db_table = "organization"
        ordering = ["title"]


class OrganizationIndexPage(Page):
    max_count = 1

    parent_page_types = ["community.CommunityPage"]
    subpage_types = ["contact.Organization"]
