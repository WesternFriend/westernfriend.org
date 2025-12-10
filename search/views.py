from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from wagtail.models import Page

from magazine.models import MagazineArticle
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

        # Optimize by grouping pages by content type to avoid double-fetching
        # Magazine articles need special optimization, fetch them separately
        from django.contrib.contenttypes.models import ContentType

        magazine_article_ct = ContentType.objects.get_for_model(MagazineArticle)

        # Separate magazine articles from other page types
        magazine_article_pages = [
            p for p in paginated_results if p.content_type_id == magazine_article_ct.id
        ]
        other_pages = [
            p for p in paginated_results if p.content_type_id != magazine_article_ct.id
        ]

        specific_instances = []

        # Fetch magazine articles with all optimizations (no double-fetch)
        if magazine_article_pages:
            # Use get_queryset() to inherit all optimizations:
            # - defer_streamfields() to avoid loading large body/body_migrated fields
            # - select_related("department") for efficient department access
            # - prefetch_related("authors__author", "tags") for related data
            magazine_articles = MagazineArticle.get_queryset().filter(
                id__in=[p.id for p in magazine_article_pages],
            )
            specific_instances.extend(magazine_articles)

        # Fetch other page types using standard .specific()
        if other_pages:
            other_specific = (
                Page.objects.filter(
                    id__in=[p.id for p in other_pages],
                )
                .select_related("content_type")
                .specific()
            )
            specific_instances.extend(other_specific)

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
