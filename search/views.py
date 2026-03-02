from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from wagtail.models import Page

from magazine.models import MagazineArticle
from pagination.helpers import get_paginated_items

MAX_QUERY_LENGTH = 30  # characters
MAX_QUERY_WORDS = 5  # words


def search(request: HttpRequest) -> HttpResponse:
    search_query = request.GET.get("query", None)
    page = request.GET.get("page", "1")
    number_per_page = 25  # Increased from 10 to reduce pagination depth
    max_page_limit = 50  # Maximum page number allowed
    query_truncated = False

    # Sanitize query to prevent runaway tsquery complexity with OR operator
    if search_query:
        if len(search_query) > MAX_QUERY_LENGTH:
            search_query = search_query[:MAX_QUERY_LENGTH]
            query_truncated = True
        words = search_query.split()
        if len(words) > MAX_QUERY_WORDS:
            search_query = " ".join(words[:MAX_QUERY_WORDS])
            query_truncated = True

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
                    "query_truncated": query_truncated,
                    "max_query_words": MAX_QUERY_WORDS,
                    "max_query_length": MAX_QUERY_LENGTH,
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
    # NOTE FOR SENTRY: This section contains optimized queries.
    # All search result parent pages are bulk-prefetched to avoid N+1 from pageurl tags.
    # See SearchOptimizationTestCase.EXPECTED_TOTAL_QUERIES in search/tests.py for counts.
    if search_query and paginated_search_results:
        # Tag Sentry transaction to indicate this is an optimized query pattern
        try:
            import sentry_sdk

            sentry_sdk.set_tag("search.queries_optimized", "true")
            sentry_sdk.set_context(
                "search_optimization",
                {
                    "note": "Parent pages bulk-prefetched for all results. See SearchOptimizationTestCase in search/tests.py.",
                },
            )
        except ImportError:
            pass  # Sentry not installed, skip tagging

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
            magazine_articles = list(
                MagazineArticle.get_queryset().filter(
                    id__in=[p.id for p in magazine_article_pages],
                ),
            )

            # Bulk-annotate parent MagazineIssue instances so parent_issue
            # property can use _parent_page without triggering N+1 queries.
            # Uses prefetch_parent_issues() rather than the generic
            # Page.objects.annotate_parent_page(), which fetches deferred
            # specific instances and causes per-article queries when
            # MagazineIssue-specific fields are accessed in the template.
            MagazineArticle.prefetch_parent_issues(magazine_articles)

            specific_instances.extend(magazine_articles)

        # Fetch other page types using standard .specific()
        if other_pages:
            # Type checker doesn't recognize Wagtail's .specific() method on PageQuerySet
            other_specific = (
                Page.objects.filter(
                    id__in=[p.id for p in other_pages],
                )
                .select_related("content_type")
                .specific()  # type: ignore[attr-defined]
            )
            specific_instances.extend(other_specific)

        # Prefetch parent pages for all search results to optimize {% pageurl %} tag
        # The pageurl tag needs parent information to construct URLs, which would otherwise
        # trigger N+1 queries. We bulk fetch all unique parent pages and cache them.
        if specific_instances:
            # Collect unique parent paths (exclude root pages which have no parent)
            parent_paths = set()
            for page in specific_instances:
                if page.depth > 1:  # Not root page
                    parent_path = page.path[: -page.steplen]
                    parent_paths.add(parent_path)

            if parent_paths:
                # Bulk fetch all parent pages
                parent_pages = Page.objects.filter(path__in=parent_paths).specific()  # type: ignore[attr-defined]
                parent_map = {page.path: page for page in parent_pages}

                # Cache parent on each page by overriding get_parent() method
                # NOTE: Monkey-patching get_parent() is required because {% pageurl %} internally
                # calls it, and we can't modify Wagtail's template tag behavior. While this
                # approach can be surprising to future contributors, it's the most pragmatic
                # solution for preventing N+1 queries without modifying templates or Wagtail internals.
                for page in specific_instances:
                    if page.depth > 1:
                        parent_path = page.path[: -page.steplen]
                        if parent_path in parent_map:
                            cached_parent = parent_map[parent_path]
                            # Override get_parent method to return cached parent
                            page.get_parent = lambda cached_parent=cached_parent: (
                                cached_parent
                            )

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
            "query_truncated": query_truncated,
            "max_query_words": MAX_QUERY_WORDS,
            "max_query_length": MAX_QUERY_LENGTH,
        },
    )
