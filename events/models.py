from datetime import date

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db import models
from django.db.models import Q

from wagtail.admin.edit_handlers import FieldPanel
from wagtail.core.fields import RichTextField
from wagtail.core.models import Page
from wagtail.search import index

# Create your models here.


class Event(Page):
    description = RichTextField(blank=True)

    date = models.DateTimeField()

    website = models.URLField(blank=True, null=True)

    content_panels = Page.content_panels + [
        FieldPanel("description"),
        FieldPanel("date"),
        FieldPanel("website")
    ]

    search_template = "search/event.html"

    search_fields = [
        index.SearchField("description", partial_match=True),
    ]

    parent_page_types = ["EventsIndexPage"]
    subpage_types = []

    class Meta:
        db_table = "events"
        ordering = ["date"]


class EventsIndexPage(Page):
    intro = RichTextField(blank=True)

    content_panels = Page.content_panels + [FieldPanel("intro")]

    subpage_types = ["Event"]

    max_count = 1

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request)

        upcoming_events = Event.objects.all().filter(
            Q(date__gt=date.today())).order_by('date')

        # Show three archive issues per page
        paginator = Paginator(upcoming_events, 3)

        upcoming_events_page = request.GET.get("page")

        try:
            paginated_events = paginator.page(upcoming_events_page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            paginated_events = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            paginated_events = paginator.page(paginator.num_pages)

        context["events"] = paginated_events

        return context
