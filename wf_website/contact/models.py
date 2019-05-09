from enum import Enum

from django.db import models
from django.utils.text import slugify
from django_extensions.db.fields import AutoSlugField


from modelcluster.models import ClusterableModel
from wagtail.admin.edit_handlers import FieldPanel
from wagtail.core.models import Page
from wagtail.core.fields import RichTextField
from wagtail.search import index

CONTACT_TYPE_CHOICES = (
    ("monthly_meeting", "Monthly Meeting"),
    ("person", "Person"),
    ("quaker_organization", "Quaker Organization"),
    ("quarterly_meeting", "Quarterly Meeting"),
    ("worship_group", "Worship Group"),
    ("yearly_meeting", "Yearly Meeting"),
)


class Contact(Page):
    given_name = models.CharField(
        max_length=255,
        default="",
        help_text="Enter the given name for a person. This can also be used for an organization name.",
    )

    family_name = models.CharField(max_length=255, blank=True, default="")

    contact_type = models.CharField(
        max_length=255, choices=CONTACT_TYPE_CHOICES)

    description = models.CharField(max_length=255, blank=True, null=True)

    full_name = models.CharField(max_length=255, editable=False, null=True)

    website = models.URLField(null=True, blank=True)

    content_panels = [
        FieldPanel("given_name"),
        FieldPanel("family_name"),
        FieldPanel("description"),
        FieldPanel("website"),
        FieldPanel("contact_type"),
    ]

    class Meta:
        db_table = "contact"
        ordering = ["title"]

    def save(self, *args, **kwargs):
        full_name = f"{self.given_name} {self.family_name}"
        self.title = full_name.strip()

        super(Contact, self).save(*args, **kwargs)

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request)
        # pylint: disable=E501
        # TODO: get upcoming events
        # context['upcoming_events'] = MagazineIssue.objects.live().order_by('-publication_date').first()

        context["quarterly_meetings"] = Contact.objects.child_of(
            self).filter(contact_type="quarterly_meeting")

        context["monthly_meetings"] = Contact.objects.descendant_of(
            self).filter(contact_type="monthly_meeting")

        context["worship_groups"] = Contact.objects.descendant_of(
            self).filter(contact_type="worship_group")

        return context

    search_fields = [
        index.SearchField("given_name", partial_match=True),
        index.SearchField("family_name", partial_match=True),
    ]

    parent_page_types = ["community.CommunityPage", "Contact"]
    subpage_types = ["Contact"]
