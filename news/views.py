from wagtail.admin.viewsets.pages import PageListingViewSet
from wagtail.admin.ui.tables import DateColumn
from wagtail.admin.ui.tables.pages import (
    BulkActionsColumn,
    PageTitleColumn,
    PageStatusColumn,
)
import django_filters

from facets.models import Topic
from .models import NewsItem


class NewsItemFilterSet(PageListingViewSet.filterset_class):
    topics__topic = django_filters.ModelChoiceFilter(
        label="Topic",
        queryset=Topic.objects.all(),
    )

    class Meta:
        model = NewsItem
        fields = [
            "topics__topic",
        ]


class NewsItemViewSet(PageListingViewSet):
    model = NewsItem
    menu_label = "News Items"
    icon = "list-ul"
    add_to_admin_menu = True
    columns = [
        PageTitleColumn(
            "title",
            label="Title",
            sort_key="title",
            classname="title",
        ),
        DateColumn(
            "publication_date",
            label="Publication Date",
            sort_key="publication_date",
        ),
        PageStatusColumn(
            "live",
            label="Live",
            sort_key="live",
        ),
        BulkActionsColumn(
            "bulk_actions",
            label="Bulk Actions",
        ),
    ]
    filterset_class = NewsItemFilterSet


news_item_viewset = NewsItemViewSet("news_items")
