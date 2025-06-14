from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from wagtail.models import Page

from pagination.helpers import get_paginated_items


def search(request: HttpRequest) -> HttpResponse:
    search_query = request.GET.get("query", None)
    page = request.GET.get("page", "1")
    number_per_page = 10

    # Search
    # Using the 'or' operator to search for pages that contain any of the words
    if search_query:
        # First get the search results
        search_results = Page.objects.live().search(
            search_query,
            operator="or",
        )

        # Then apply optimizations and get specific instances
        search_results = (
            search_results.select_related(  # Fetch related fields in single query
                "owner",
                "content_type",
                "locale",
            )
            .prefetch_related(  # Prefetch related fields to avoid N+1 queries
                # For magazine articles - prefetch authors and departments
                "magazinearticle__authors__author",
                "magazinearticle__department",
                # For magazine issues - prefetch cover images
                "magazineissue__cover_image",
                # For archive articles - prefetch authors
                "archivearticle__archive_authors__author",
            )
            .specific()  # Get specific page types
        )
    else:
        search_results = Page.objects.none()

    paginated_search_results = get_paginated_items(
        search_results,
        number_per_page,
        page,
    )

    return render(
        request,
        "search/search.html",
        {
            "search_query": search_query,
            "search_querystring": f"query={search_query}",
            "paginated_search_results": paginated_search_results,
        },
    )
