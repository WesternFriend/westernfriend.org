from django.core.cache import cache
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from wagtail.models import Page

from pagination.helpers import get_paginated_items


def search(request: HttpRequest) -> HttpResponse:
    search_query = request.GET.get("query", None)
    page = request.GET.get("page", "1")
    number_per_page = 25  # Increased from 10 to reduce pagination depth
    max_page_limit = 50  # Maximum page number allowed

    # Search
    # Using the 'or' operator to search for pages that contain any of the words
    if search_query:
        # Check if requested page exceeds limit
        page_number = int(page) if page.isdigit() else 1
        if page_number > max_page_limit:
            return render(
                request,
                "search/search.html",
                {
                    "search_query": search_query,
                    "search_querystring": f"query={search_query}",
                    "paginated_search_results": None,
                    "page_limit_exceeded": True,
                    "max_page_limit": max_page_limit,
                },
            )

        # Try to get cached results
        cache_key = f"search:{search_query}:{page}:{number_per_page}"
        cached_results = cache.get(cache_key)

        if cached_results is not None:
            return render(
                request,
                "search/search.html",
                cached_results,
            )

        # Build an optimized queryset and then search it
        search_results = (
            Page.objects.live()  # type: ignore[attr-defined]
            .only(
                "id",
                "content_type_id",
                "title",
                "url_path",
                "slug",
                "live",
            )  # Reduce data fetched during initial search
            .select_related(  # Fetch related fields in single query
                "content_type",
            )
            .search(
                search_query,
                operator="or",
            )
        )
    else:
        search_results = Page.objects.none()

    paginated_search_results = get_paginated_items(
        search_results,
        number_per_page,
        page,
    )

    # Call .specific() only on the paginated slice to reduce overhead
    if search_query:
        paginated_results = paginated_search_results.page.object_list
        specific_results = [result.specific for result in paginated_results]

        # Replace the object_list with specific instances
        paginated_search_results.page.object_list = specific_results

    context = {
        "search_query": search_query,
        "search_querystring": f"query={search_query}",
        "paginated_search_results": paginated_search_results,
    }

    # Cache results for 10 minutes
    if search_query:
        cache.set(cache_key, context, 600)

    return render(
        request,
        "search/search.html",
        context,
    )
