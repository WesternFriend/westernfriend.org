from django.core.cache import cache
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from wagtail.models import Page

from pagination.helpers import get_paginated_items


def search(request: HttpRequest) -> HttpResponse:
    search_query = request.GET.get("query", None)
    page = request.GET.get("page", "1")
    number_per_page = 10

    # Build a cache key based on the search query
    cache_key = None
    if search_query:
        # Normalize the query for caching (lowercase, strip extra spaces)
        normalized_query = " ".join(search_query.lower().split())
        cache_key = f"search_results_{normalized_query}"

    # Search
    # Using the 'or' operator to search for pages that contain any of the words
    if search_query:
        # Try to get results from cache first (only for first page of results)
        search_results = None
        if page == "1" and cache_key:
            search_results = cache.get(cache_key)

        # If not in cache, perform the search
        if search_results is None:
            search_results = (
                Page.objects.live()
                .specific()  # Get specific page types in single query
                .select_related(  # Fetch direct related fields in single query
                    "owner",
                    "content_type",
                    "locale",
                )
                .prefetch_related(  # Prefetch many-to-many relationships to reduce queries
                    "tags",  # Common for magazine articles, news items, library items
                    "magazine_articles_authored",  # For Person pages that authored articles
                    "library_items_authored",  # For Person pages that authored library items
                    "magazine_articles_department",  # For magazine department relationship
                    "tagged_items",  # For tag relationships
                )
                .search(
                    search_query,
                    operator="or",
                    score=True,  # Return search scores for better sorting
                )
                .order_by("-_score")  # Sort by relevance score
            )

            # Cache the results for 1 hour (for first page only)
            if page == "1" and cache_key:
                cache.set(cache_key, search_results, 60 * 60)  # 1 hour cache
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
