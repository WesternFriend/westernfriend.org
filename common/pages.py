def live_specific_pages(pages):
    """Return specific pages that are still published.

    ``QuerySet.specific()`` loads each concrete model by primary key and does
    not repeat the ``live()`` filter. A page unpublished after that first query
    would otherwise stay on the public page.
    """
    return [page for page in pages.live().specific() if page.live]
