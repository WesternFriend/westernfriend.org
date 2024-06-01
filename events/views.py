from wagtail.admin.ui.tables import Column
from wagtail.admin.viewsets.pages import PageListingViewSet

from .models import Event


class EventViewSet(PageListingViewSet):
    model = Event
    menu_label = "Events"
    icon = "date"
    name = "events"
    columns = [
        Column(
            "title",
            label="Title",
            sort_key="title",
        ),
        Column(
            "start_date",
            label="Start Date",
            sort_key="start_date",
        ),
        Column(
            "end_date",
            label="End Date",
            sort_key="end_date",
        ),
    ]
    search_fields = ["title"]
    ordering = ["-start_date"]
