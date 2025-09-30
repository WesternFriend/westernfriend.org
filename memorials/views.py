from wagtail.admin.ui.tables import Column
from wagtail.admin.ui.tables.pages import BulkActionsColumn, PageTitleColumn
from wagtail.admin.viewsets.pages import PageListingViewSet

from .models import Memorial


class MemorialViewSet(PageListingViewSet):
    model = Memorial
    menu_label = "Memorials"
    name = "memorials"
    icon = "user"
    columns = [
        BulkActionsColumn(
            "id",
        ),
        PageTitleColumn(
            "title",
            label="Title",
            sort_key="title",
            classname="title",
        ),
        Column(
            "memorial_person",
            label="Person",
            sort_key="memorial_person",
        ),
        Column(
            "memorial_meeting",
            label="Meeting",
            sort_key="memorial_meeting",
        ),
    ]
    search_fields = ["full_name", "memorial_meeting"]
