from django.db import models

from django_extensions.db.fields import AutoSlugField
from modelcluster.models import ClusterableModel
from wagtail.search import index


class Author(index.Indexed, ClusterableModel):
    given_name = models.CharField(
        max_length=255,
        default='',
        help_text="Enter the given name for a person. This can also be used for an organization name."
    )
    family_name = models.CharField(
        max_length=255,
        blank=True,
        default='',
    )
    slug = AutoSlugField(
        null=True,
        blank=True,
        populate_from=[
            'given_name',
            'family_name',
        ]
    )

    autocomplete_search_field = 'given_name'

    def autocomplete_label(self):
        return self.__str__()

    def __str__(self):
        return f"{self.given_name} {self.family_name}"

    class Meta:
        db_table = 'author'

    search_fields = [
        index.SearchField('given_name', partial_match=True),
        index.SearchField('family_name', partial_match=True),
    ]
