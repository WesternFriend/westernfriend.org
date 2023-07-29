from django.core.paginator import Paginator, Page
from django.db.models import QuerySet


def get_paginated_items(
    items: QuerySet,
    items_per_page: int,
    page_number: str = "1",
) -> Page:
    """Paginate items and return a page of items."""

    paginator: Paginator = Paginator(items, items_per_page)

    paginator_page_number = 1

    # Make sure page is numeric
    # and less than or equal to the total pages
    if page_number.isdigit() and int(page_number) <= paginator.num_pages:
        paginator_page_number = int(page_number)

    return paginator.page(paginator_page_number)
