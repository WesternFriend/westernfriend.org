from typing import Any
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.db.models import TextChoices
from modelcluster.fields import ParentalKey
from wagtail.admin.panels import (
    FieldPanel,
    FieldRowPanel,
    InlinePanel,
    PageChooserPanel,
)
from wagtail.fields import RichTextField
from wagtail.models import Orderable, Page
from wagtail.search import index

from addresses.models import Address


class Person(Page):
    given_name = models.CharField(
        max_length=255,
        default="",
        help_text="Enter the given name for a person.",
        null=True,
        blank=True,
    )

    family_name = models.CharField(
        max_length=255,
        blank=True,
        default="",
    )
    drupal_author_id = models.IntegerField(
        null=True,
        blank=True,
        unique=True,
        db_index=True,
    )
    drupal_duplicate_author_ids = ArrayField(
        models.IntegerField(),
        blank=True,
        default=list,
    )
    drupal_library_author_id = models.IntegerField(
        null=True,
        blank=True,
        db_index=True,
    )
    civicrm_id = models.IntegerField(
        null=True,
        blank=True,
        db_index=True,
    )

    content_panels = [
        FieldPanel("given_name"),
        FieldPanel("family_name"),
        FieldRowPanel(
            heading="Import metadata",
            help_text="Temporary area for troubleshooting content importers.",
            children=[
                FieldPanel(
                    "civicrm_id",
                    permission="superuser",
                ),
                FieldPanel(
                    "drupal_author_id",
                    permission="superuser",
                ),
                FieldPanel(
                    "drupal_duplicate_author_ids",
                    permission="superuser",
                ),
            ],
        ),
    ]

    template = "contact/contact.html"

    class Meta:
        db_table = "person"
        ordering = ["title"]
        verbose_name_plural = "people"
        indexes = [
            models.Index(fields=["civicrm_id"]),
            models.Index(fields=["drupal_author_id"]),
        ]

    def save(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        full_name = f"{self.given_name} {self.family_name}"
        self.title = full_name.strip()

        super().save(*args, **kwargs)

    search_fields = Page.search_fields + [
        index.SearchField(
            "given_name",
        ),
        index.SearchField(
            "family_name",
        ),
        index.SearchField(
            "drupal_author_id",
        ),
    ]

    parent_page_types = ["contact.PersonIndexPage"]
    subpage_types: list[str] = []


class PersonIndexPage(Page):
    max_count = 1

    parent_page_types = ["community.CommunityPage"]
    subpage_types: list[str] = ["contact.Person"]

    template = "contact/person_index_page.html"


class MeetingPresidingClerk(Orderable):
    """Presiding clerk of Quaker meeting."""

    meeting = ParentalKey(
        "contact.Meeting",
        related_name="presiding_clerks",
    )
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
    class MeetingTypeChoices(TextChoices):
        MONTHLY_MEETING = "monthly_meeting", "Monthly Meeting"
        QUARTERLY_MEETING = "quarterly_meeting", "Quarterly Meeting"
        WORSHIP_GROUP = "worship_group", "Worship Group"
        YEARLY_MEETING = "yearly_meeting", "Yearly Meeting"

    meeting_type = models.CharField(
        max_length=255,
        choices=MeetingTypeChoices.choices,
        null=True,
        blank=True,
    )
    description = RichTextField(
        blank=True,
        null=True,
    )
    website = models.URLField(
        null=True,
        blank=True,
    )
    email = models.EmailField(
        null=True,
        blank=True,
    )
    phone = models.CharField(
        max_length=64,
        null=True,
        blank=True,
    )
    civicrm_id = models.IntegerField(
        null=True,
        blank=True,
        db_index=True,
    )
    drupal_author_id = models.IntegerField(
        null=True,
        blank=True,
        unique=True,
        db_index=True,
    )
    drupal_duplicate_author_ids = ArrayField(
        models.IntegerField(),
        blank=True,
        default=list,
    )
    drupal_library_author_id = models.IntegerField(
        null=True,
        blank=True,
        db_index=True,
    )
    information_last_verified = models.DateField(
        null=True,
        blank=True,
    )

    content_panels = Page.content_panels + [
        FieldPanel("description"),
        FieldPanel("website"),
        FieldPanel("email"),
        FieldPanel("phone"),
        FieldPanel("meeting_type"),
        InlinePanel("worship_times", label="Worship times"),
        InlinePanel("addresses", label="Address"),
        InlinePanel(
            "presiding_clerks",
            label="Presiding clerk",
            heading="Presiding clerk(s)",
        ),
        FieldPanel("information_last_verified"),
        FieldRowPanel(
            heading="Import metadata",
            help_text="Temporary area for troubleshooting content importers.",
            children=[
                FieldPanel(
                    "civicrm_id",
                    permission="superuser",
                    read_only=True,
                ),
                FieldPanel(
                    "drupal_author_id",
                    permission="superuser",
                    read_only=True,
                ),
                FieldPanel(
                    "drupal_duplicate_author_ids",
                    permission="superuser",
                    read_only=True,
                ),
            ],
        ),
    ]

    parent_page_types = ["contact.MeetingIndexPage", "Meeting"]
    subpage_types: list[str] = ["Meeting"]

    template = "contact/contact.html"

    search_template = "search/meeting.html"

    search_fields = Page.search_fields + [
        index.SearchField(
            "description",
        ),
        index.SearchField(
            "drupal_author_id",
        ),
    ]

    class Meta:
        db_table = "meeting"
        ordering = ["title"]
        indexes = [
            models.Index(fields=["civicrm_id"]),
            models.Index(fields=["drupal_author_id"]),
        ]

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request)

        context["quarterly_meetings"] = (
            Meeting.objects.child_of(self)
            .filter(meeting_type="quarterly_meeting")
            .order_by("title")
        )

        context["monthly_meetings"] = (
            Meeting.objects.descendant_of(self)
            .filter(meeting_type="monthly_meeting")
            .order_by("title")
        )

        context["worship_groups"] = (
            Meeting.objects.descendant_of(self)
            .filter(meeting_type="worship_group")
            .order_by("title")
        )

        return context


class MeetingAddress(Orderable, Address):
    page = ParentalKey(
        "contact.Meeting",
        on_delete=models.CASCADE,
        related_name="addresses",
    )


class WorshipTypeChoices(models.TextChoices):
    FIRST_DAY_WORSHIP = "first_day_worship", "First day worship"
    FIRST_DAY_WORSHIP_2ND = "first_day_worship_2nd", "First day worship, 2nd"
    BUSINESS_MEETING = "business_meeting", "Business meeting"
    OTHER_REGULAR_MEETING = "other_regular_meeting", "Other regular meeting"


class MeetingWorshipTime(Orderable):
    meeting = ParentalKey(
        "contact.Meeting",
        on_delete=models.CASCADE,
        related_name="worship_times",
    )
    worship_type = models.CharField(
        max_length=255,
        choices=WorshipTypeChoices.choices,
        null=True,
        blank=True,
    )
    worship_time = models.CharField(max_length=255)


class MeetingIndexPage(Page):
    max_count = 1

    parent_page_types = ["community.CommunityPage"]
    subpage_types: list[str] = ["contact.Meeting"]

    template = "contact/meeting_index_page.html"


class Organization(Page):
    description = models.CharField(
        max_length=255,
        blank=True,
        null=True,
    )

    website = models.URLField(
        null=True,
        blank=True,
    )
    civicrm_id = models.IntegerField(
        null=True,
        blank=True,
        db_index=True,
    )
    drupal_author_id = models.IntegerField(
        null=True,
        blank=True,
        unique=True,
        db_index=True,
    )
    drupal_duplicate_author_ids = ArrayField(
        models.IntegerField(),
        blank=True,
        default=list,
    )
    drupal_library_author_id = models.IntegerField(
        null=True,
        blank=True,
        db_index=True,
    )

    content_panels = Page.content_panels + [
        FieldPanel("description"),
        FieldPanel("website"),
        FieldRowPanel(
            heading="Import metadata",
            help_text="Temporary area for troubleshooting content importers.",
            children=[
                FieldPanel(
                    "civicrm_id",
                    permission="superuser",
                ),
                FieldPanel(
                    "drupal_author_id",
                    permission="superuser",
                ),
                FieldPanel(
                    "drupal_duplicate_author_ids",
                    permission="superuser",
                ),
            ],
        ),
    ]

    parent_page_types = ["contact.OrganizationIndexPage"]
    subpage_types: list[str] = []

    template = "contact/contact.html"

    search_template = "search/organization.html"

    search_fields = Page.search_fields + [
        index.SearchField(
            "description",
        ),
        index.SearchField(
            "drupal_author_id",
        ),
    ]

    class Meta:
        db_table = "organization"
        ordering = ["title"]
        indexes = [
            models.Index(fields=["civicrm_id"]),
            models.Index(fields=["drupal_author_id"]),
        ]


class OrganizationIndexPage(Page):
    max_count = 1

    parent_page_types = ["community.CommunityPage"]
    subpage_types: list[str] = ["contact.Organization"]
