from django.db import models
from django.http import HttpRequest
from django_flatpickr.widgets import DatePickerInput
from wagtail.admin.panels import FieldPanel, PageChooserPanel
from wagtail.fields import RichTextField
from wagtail.models import Page

from contact.models import Meeting
from common.models import DrupalFields
from pagination.helpers import get_paginated_items


class Memorial(DrupalFields, Page):  # type: ignore
    memorial_person = models.ForeignKey(
        to="contact.Person",
        on_delete=models.PROTECT,
        related_name="memorial_minute",
    )
    date_of_birth = models.DateField(null=True, blank=True)
    date_of_death = models.DateField(null=True, blank=True)
    dates_are_approximate = models.BooleanField(default=False)
    memorial_minute = RichTextField(blank=True)
    memorial_meeting = models.ForeignKey(
        to="contact.Meeting",
        on_delete=models.PROTECT,
        related_name="memorial_minutes",
        null=True,
        blank=True,
    )
    drupal_memorial_id = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        ordering = (
            "memorial_person__family_name",
            "memorial_person__given_name",
        )

    def full_name(self) -> str:
        return (
            f"{ self.memorial_person.given_name } { self.memorial_person.family_name }"
        )

    content_panels = Page.content_panels + [
        PageChooserPanel("memorial_person"),
        FieldPanel("date_of_birth", widget=DatePickerInput()),
        FieldPanel("date_of_death", widget=DatePickerInput()),
        FieldPanel("dates_are_approximate"),
        FieldPanel("memorial_minute"),
        PageChooserPanel("memorial_meeting"),
    ]

    parent_page_types = [
        "memorials.MemorialIndexPage",
    ]

    # TODO: determine whether we need a search index on any of the fields
    # or remove this search fields code
    # search_fields = []


class MemorialIndexPage(Page):
    intro = RichTextField(blank=True)

    max_count = 1

    content_panels = Page.content_panels + [FieldPanel("intro")]

    parent_page_types = ["community.CommunityPage"]
    subpage_types: list[str] = [
        "memorials.Memorial",
    ]

    def get_filtered_memorials(
        self,
        query: dict,
    ) -> models.QuerySet[Memorial]:
        # Filter out any facet that isn't a model field
        allowed_keys = [
            "title",
            "memorial_meeting__title",
        ]
        facets = {
            f"{key}__icontains": query[key] for key in query if key in allowed_keys
        }

        return Memorial.objects.all().filter(**facets)

    def get_context(
        self,
        request: HttpRequest,
        *args: tuple,
        **kwargs: dict,
    ) -> dict:
        context = super().get_context(request)

        filtered_memorials = self.get_filtered_memorials(
            query=request.GET.dict(),
        )

        items_per_page = 10
        page_number = request.GET.get("page", "1")

        context["memorials"] = get_paginated_items(
            items=filtered_memorials,
            items_per_page=items_per_page,
            page_number=page_number,
        )

        # Populate faceted search fields
        context["meetings"] = Meeting.objects.all()

        return context
