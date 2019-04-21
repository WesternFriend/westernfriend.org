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
    ("worship_group", "Worship Group"),
    ("yearly_meeting", "Yearly Meeting"),
)


class Contact(index.Indexed, ClusterableModel):
    given_name = models.CharField(
        max_length=255,
        default="",
        help_text="Enter the given name for a person. This can also be used for an organization name.",
    )

    family_name = models.CharField(max_length=255, blank=True, default="")

    contact_type = models.CharField(max_length=255, choices=CONTACT_TYPE_CHOICES)

    slug = AutoSlugField(
        null=True,
        blank=True,
        populate_from=["given_name", "family_name"],
        overwrite=True,
    )
    full_name = models.CharField(max_length=255, editable=False, null=True)

    content_panels = [
        FieldPanel("given_name"),
        FieldPanel("family_name"),
        FieldPanel("contact_type"),
    ]

    autocomplete_search_field = "full_name"

    class Meta:
        db_table = "contact"

    def __str__(self):
        return f"{self.given_name} {self.family_name}"

    def autocomplete_label(self):
        return self.full_name

    def save(self, *args, **kwargs):
        self.full_name = f"{self.given_name} {self.family_name}"

        super(Contact, self).save(*args, **kwargs)

    search_fields = [
        index.SearchField("given_name", partial_match=True),
        index.SearchField("family_name", partial_match=True),
        index.SearchField("family_name", partial_match=True),
    ]
