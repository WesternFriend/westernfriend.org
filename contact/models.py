from typing import Any

from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.db.models import TextChoices
from django.utils.encoding import force_str
from django.utils.html import strip_tags
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


class JSONLDMixin:
    def get_json_ld(self):
        data = {
            "@context": "https://schema.org",
            "name": force_str(self.title),
        }

        if hasattr(self, "description"):
            data["description"] = strip_tags(force_str(self.description))

        if hasattr(self, "website") and self.website:
            data["url"] = self.website
        if hasattr(self, "email") and self.email:
            data["email"] = self.email
        if hasattr(self, "phone") and self.phone:
            data["telephone"] = self.phone

        if hasattr(self, "addresses") and self.addresses.count():
            data["address"] = []
            for address in self.addresses.all():
                address_data = {
                    "@type": "PostalAddress",
                }
                if address.street_address:
                    address_data["streetAddress"] = force_str(address.street_address)
                    if address.extended_address:
                        address_data["streetAddress"] += ", " + force_str(
                            address.extended_address,
                        )
                    if address.po_box_number:
                        address_data["streetAddress"] += ", P.O. Box " + force_str(
                            address.po_box_number,
                        )
                if address.locality:
                    address_data["addressLocality"] = force_str(address.locality)
                if address.region:
                    address_data["addressRegion"] = force_str(address.region)
                if address.postal_code:
                    address_data["postalCode"] = force_str(address.postal_code)
                if address.country:
                    address_data["addressCountry"] = force_str(address.country)
                if address.latitude and address.longitude:
                    address_data["geo"] = {
                        "@type": "GeoCoordinates",
                        "latitude": address.latitude,
                        "longitude": address.longitude,
                    }
                data["address"].append(address_data)

        return data


class ContactBase(JSONLDMixin, Page):
    """
    Abstract base class for all contact types (Person, Meeting, Organization)
    """

    website = models.URLField(
        null=True,
        blank=True,
        help_text="Website URL for this contact",
    )
    email = models.EmailField(
        null=True,
        blank=True,
        help_text="Email address for this contact",
    )
    phone = models.CharField(
        max_length=64,
        null=True,
        blank=True,
        help_text="Phone number for this contact",
    )

    # Fields for external system integration
    civicrm_id = models.IntegerField(
        null=True,
        blank=True,
        db_index=True,
        help_text="ID in the CiviCRM system",
    )
    drupal_author_id = models.IntegerField(
        null=True,
        blank=True,
        unique=True,
        db_index=True,
        help_text="ID of the author in Drupal",
    )
    drupal_duplicate_author_ids = ArrayField(
        models.IntegerField(),
        blank=True,
        default=list,
        help_text="IDs of duplicate authors in Drupal",
    )
    drupal_library_author_id = models.IntegerField(
        null=True,
        blank=True,
        db_index=True,
        help_text="ID of the library author in Drupal",
    )

    # Common panels for all contact types
    import_metadata_panels = [
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
    ]

    base_content_panels = Page.content_panels + [
        FieldPanel("website"),
        FieldPanel("email"),
        FieldPanel("phone"),
        FieldRowPanel(
            heading="Import metadata",
            help_text="Temporary area for troubleshooting content importers.",
            children=import_metadata_panels,
        ),
    ]

    base_search_fields = Page.search_fields + [
        index.SearchField("drupal_author_id"),
    ]

    template = "contact/contact.html"

    class Meta:
        abstract = True
        ordering = ["title"]
        indexes = [
            models.Index(fields=["civicrm_id"]),
            models.Index(fields=["drupal_author_id"]),
        ]


class Person(ContactBase):
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

    content_panels = Page.content_panels + [
        FieldPanel("given_name"),
        FieldPanel("family_name"),
        FieldPanel("website"),
        FieldPanel("email"),
        FieldPanel("phone"),
        FieldRowPanel(
            heading="Import metadata",
            help_text="Temporary area for troubleshooting content importers.",
            children=ContactBase.import_metadata_panels,
        ),
    ]

    template = "contact/contact.html"

    def save(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        # Both given name and family name can technically be empty
        full_name = f"{self.given_name} {self.family_name}"
        # So, we fall back to using "Unnamed Person" to make sure we have a title value
        self.title = full_name.strip() or "Unnamed Person"

        super().save(*args, **kwargs)

    search_fields = ContactBase.base_search_fields + [
        index.SearchField("given_name"),
        index.SearchField("family_name"),
    ]

    parent_page_types = ["contact.PersonIndexPage"]
    subpage_types: list[str] = []

    def get_json_ld(self):
        data = super().get_json_ld()
        data.update(
            {
                "@type": "Person",
                "givenName": force_str(self.given_name),
                "familyName": force_str(self.family_name),
            },
        )
        return data

    class Meta:
        db_table = "person"
        verbose_name_plural = "people"
        ordering = ["title"]
        indexes = [
            models.Index(fields=["civicrm_id"]),
            models.Index(fields=["drupal_author_id"]),
        ]


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


class Meeting(ContactBase):
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
            children=ContactBase.import_metadata_panels,
        ),
    ]

    parent_page_types = ["contact.MeetingIndexPage", "Meeting"]
    subpage_types: list[str] = ["Meeting"]

    search_template = "search/meeting.html"

    search_fields = ContactBase.base_search_fields + [
        index.SearchField("description"),
    ]

    class Meta:
        db_table = "meeting"
        ordering = ["title"]
        indexes = [
            models.Index(fields=["civicrm_id"]),
            models.Index(fields=["drupal_author_id"]),
        ]

    template = "contact/contact.html"

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

    def get_json_ld(self):
        data = super().get_json_ld()
        data.update(
            {
                "@type": "Organization",
                "organizationType": force_str(self.get_meeting_type_display()),
            },
        )

        if self.worship_times.count():
            data["event"] = []
            for worship_time in self.worship_times.all():
                event_data = {
                    "@type": "Event",
                    "name": force_str(worship_time.get_worship_type_display()),
                    "description": force_str(worship_time.worship_time),
                }
                data["event"].append(event_data)

        return data


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


class Organization(ContactBase):
    description = models.CharField(
        max_length=255,
        blank=True,
        null=True,
    )

    content_panels = Page.content_panels + [
        FieldPanel("description"),
        FieldPanel("website"),
        FieldPanel("email"),
        FieldPanel("phone"),
        FieldRowPanel(
            heading="Import metadata",
            help_text="Temporary area for troubleshooting content importers.",
            children=ContactBase.import_metadata_panels,
        ),
    ]

    parent_page_types = ["contact.OrganizationIndexPage"]
    subpage_types: list[str] = []

    template = "contact/contact.html"
    search_template = "search/organization.html"

    search_fields = ContactBase.base_search_fields + [
        index.SearchField("description"),
    ]

    class Meta:
        db_table = "organization"
        ordering = ["title"]
        indexes = [
            models.Index(fields=["civicrm_id"]),
            models.Index(fields=["drupal_author_id"]),
        ]

    def get_json_ld(self):
        data = super().get_json_ld()
        data["@type"] = "Organization"
        return data


class OrganizationIndexPage(Page):
    max_count = 1

    parent_page_types = ["community.CommunityPage"]
    subpage_types: list[str] = ["contact.Organization"]
