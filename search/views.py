from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from wagtail.models import Page
from wagtail.search.models import Query

from pagination.helpers import get_paginated_items


def search(request: HttpRequest) -> HttpResponse:
    search_query = request.GET.get("query", None)
    page = request.GET.get("page", "1")

    # Search
    if search_query:
        search_results = Page.objects.live().search(search_query)
        query = Query.get(search_query)

        # Record hit
        query.add_hit()
    else:
        search_results = Page.objects.none()

    paginated_search_results = get_paginated_items(
        search_results,
        10,
        page,
    )

    return render(
        request,
        "search/search.html",
        {
            "search_query": search_query,
            "paginated_search_results": paginated_search_results,
        },
    )
