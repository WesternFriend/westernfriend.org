from dataclasses import dataclass
from collections.abc import Iterator
from django.core.paginator import Paginator, Page
from django.db.models import QuerySet


@dataclass
class PaginatorPageWithElidedPageRange:
    """A page of items with an elided page range."""

    page: Page
    elided_page_range: Iterator[int | str]


def get_paginated_items(
    items: QuerySet,
    items_per_page: int,
    page_number: int = 1,
) -> PaginatorPageWithElidedPageRange:
    """Paginate items and return a page of items."""

    paginator: Paginator = Paginator(items, items_per_page)

    paginator_page_number = (
        page_number if 1 <= page_number <= paginator.num_pages else 1
    )

    elided_page_range = paginator.get_elided_page_range(
        paginator_page_number,
    )

    return PaginatorPageWithElidedPageRange(
        page=paginator.page(paginator_page_number),
        elided_page_range=elided_page_range,
    )
