import django_filters
from wagtail.admin.filters import DateRangePickerWidget, WagtailFilterSet
from wagtail.admin.ui.tables.pages import BulkActionsColumn, PageTitleColumn
from wagtail.admin.viewsets.base import ViewSetGroup
from wagtail.admin.viewsets.model import ModelViewSet
from wagtail.admin.viewsets.pages import PageListingViewSet

from orders.models import Order
from .models import Book


class BookViewSet(PageListingViewSet):
    model = Book
    menu_label = "Books"
    icon = "openquote"
    name = "books"
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
    ]
    search_fields = ["title"]
    ordering = ["title"]


class OrderFilterSet(WagtailFilterSet):
    created_at = django_filters.DateFromToRangeFilter(
        label="Created At",
        widget=DateRangePickerWidget,
    )

    class Meta:
        model = Order
        fields = [
            "created_at",
            "paid",
        ]


class OrderViewSet(ModelViewSet):
    model = Order
    menu_label = "Orders"
    icon = "tasks"
    name = "bookstore_orders"
    list_display = (
        "created_at",
        "purchaser_email",
        "purchaser_full_name",
        "paid",
        "paypal_transaction_id",
    )
    inspect_view_enabled = True
    inspect_view_fields = [
        "id",
        "paid",
        "purchaser_given_name",
        "purchaser_family_name",
        "purchaser_meeting_or_organization",
        "recipient_name",
        "recipient_street_address",
        "recipient_postal_code",
        "recipient_address_locality",
        "recipient_address_region",
        "recipient_address_country",
        "items",
    ]
    search_fields = [
        "purchaser_email",
        "purchaser_given_name",
        "purchaser_family_name",
        "purchaser_meeting_or_organization",
        "recipient_name",
        "paypal_transaction_id",
    ]
    ordering = ["-created_at"]
    filterset_class = OrderFilterSet


class StoreViewSetGroup(ViewSetGroup):
    menu_label = "Bookstore"
    menu_icon = "openquote"
    name = "store"
    menu_order = 200
    items = [
        BookViewSet,
        OrderViewSet,
    ]
