from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db import models

from wagtail.admin.edit_handlers import FieldPanel, PageChooserPanel
from wagtail.core.fields import RichTextField
from wagtail.core.models import Page
from wagtail.search import index

from flatpickr import DatePickerInput

from contact.models import Meeting


class Memorial(Page):
    memorial_person = models.ForeignKey(
        to="contact.Person",
        on_delete=models.PROTECT,
        related_name="memorial_minute",
    )
    date_of_birth = models.DateField()
    date_of_death = models.DateField()
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

    def full_name(self):
        return f"{ self.memorial_person.given_name } { self.memorial_person.family_name }"

    content_panels = [
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

    def save(self, *args, **kwargs):
        self.title = self.full_name()

        super(Memorial, self).save(*args, **kwargs)

    # TODO: determine whether we need a search index on any of the fields
    # or remove this search fields code
    # search_fields = []


class MemorialIndexPage(Page):
    intro = RichTextField(blank=True)

    max_count = 1

    content_panels = Page.content_panels + [
        FieldPanel("intro")
    ]

    parent_page_types = ["community.CommunityPage"]
    subpage_types = [
        "memorials.Memorial",
    ]

    def get_filtered_memorials(self, request):
        # Check if any query string is available
        query = request.GET.dict()

        # Filter out any facet that isn't a model field
        allowed_keys = [
            "title",
            "memorial_meeting__title",
        ]
        facets = {f"{key}__icontains": query[key]
                  for key in query if key in allowed_keys}

        return Memorial.objects.all().filter(**facets)

    def get_paginated_memorials(self, filtered_memorials, request):
        items_per_page = 10

        paginator = Paginator(filtered_memorials, items_per_page)

        memorials_page = request.GET.get("page")

        try:
            paginated_memorials = paginator.page(memorials_page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            paginated_memorials = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            paginated_memorials = paginator.page(paginator.num_pages)

        return paginated_memorials

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request)

        filtered_memorials = self.get_filtered_memorials(request)

        paginated_memorials = self.get_paginated_memorials(filtered_memorials, request)

        context["memorials"] = paginated_memorials

        # Populate faceted search fields
        context["meetings"] = Meeting.objects.all()

        return context
