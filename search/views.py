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

        # Build an optimized queryset and then search it
        search_results = (
            Page.objects.live()  # type: ignore[attr-defined]
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

    # Optimize specific page loading with prefetch_related for common patterns
    if search_query and paginated_search_results:
        # Get the base queryset for the paginated results
        paginated_results = paginated_search_results.page.object_list

        # Use Wagtail's bulk specific() method to fetch all specific types efficiently
        # Also prefetch common related data to avoid N+1 queries
        # Note: Only magazine articles have complex relationships (authors, parent issue)
        # Other content types (events, meetings, library items, etc.) only access
        # simple fields, so no additional prefetching is needed for them
        base_queryset = Page.objects.filter(
            id__in=[p.id for p in paginated_results],
        ).select_related(
            # Fetch content type for all pages
            "content_type",
            # Fetch parent pages (used by magazine articles to get issue info)
            "parent_page",
        )

        # Get specific instances
        specific_instances = list(base_queryset.specific())

        # Apply prefetch to the specific instances
        # This must be done after .specific() to work on the concrete model instances
        from magazine.models import MagazineArticle

        magazine_article_ids = [
            page.id for page in specific_instances if isinstance(page, MagazineArticle)
        ]

        if magazine_article_ids:
            # Re-fetch magazine articles using get_queryset() to inherit all optimizations:
            # - defer_streamfields() to avoid loading large body/body_migrated fields
            # - select_related("department") for efficient department access
            # - prefetch_related("authors__author", "tags") for related data
            prefetched_articles = MagazineArticle.get_queryset().filter(
                id__in=magazine_article_ids,
            )

            # Create mapping for replacement
            article_map = {article.id: article for article in prefetched_articles}

            # Replace magazine articles with prefetched versions
            specific_instances = [
                article_map.get(page.id, page)
                if isinstance(page, MagazineArticle)
                else page
                for page in specific_instances
            ]

        # Create a mapping of page IDs to specific instances
        specific_map = {page.id: page for page in specific_instances}

        # Replace with specific instances in the same order
        paginated_search_results.page.object_list = [
            specific_map.get(p.id, p) for p in paginated_results
        ]

    return render(
        request,
        "search/search.html",
        {
            "search_query": search_query,
            "search_querystring": f"query={search_query}",
            "paginated_search_results": paginated_search_results,
        },
    )
