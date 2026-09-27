from wagtail.models import Page


def get_library_items_for_facet(facet_instance, filter_field):
    """Helper to get library items filtered by facet with consistent ordering.

    Args:
        facet_instance: The facet page instance (Audience, Genre, Medium, or TimePeriod)
        filter_field: The field name to filter on (e.g., "item_audience")

    Returns:
        QuerySet of LibraryItem objects filtered by the facet, ordered by publication date,
        with authors prefetched to avoid N+1 queries.
    """
    # Avoid circular import
    from library.models import LibraryItem

    return (
        LibraryItem.objects.live()
        .filter(**{filter_field: facet_instance})
        .order_by("-publication_date")
        .prefetch_related("authors__author")
    )


class ChildPagesMixin:
    """Mixin that provides a child_pages context variable for index pages."""

    template = "facets/facet_index_page.html"

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        context["child_pages"] = self.get_children().live().order_by("title")
        return context


class FacetIndexPage(ChildPagesMixin, Page):
    parent_page_types = ["library.LibraryIndexPage"]
    subpage_types: list[str] = [
        "AudienceIndexPage",
        "GenreIndexPage",
        "MediumIndexPage",
        "TimePeriodIndexPage",
        "TopicIndexPage",
    ]

    max_count = 1


class AudienceIndexPage(ChildPagesMixin, Page):
    parent_page_types = ["FacetIndexPage"]
    subpage_types: list[str] = ["Audience"]

    max_count = 1


class Audience(Page):
    parent_page_types = ["AudienceIndexPage"]
    subpage_types: list[str] = []

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        context["library_items"] = get_library_items_for_facet(self, "item_audience")
        return context


class GenreIndexPage(ChildPagesMixin, Page):
    parent_page_types = ["FacetIndexPage"]
    subpage_types: list[str] = ["Genre"]

    max_count = 1


class Genre(Page):
    parent_page_types = ["GenreIndexPage"]
    subpage_types: list[str] = []

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        context["library_items"] = get_library_items_for_facet(self, "item_genre")
        return context


class MediumIndexPage(ChildPagesMixin, Page):
    parent_page_types = ["FacetIndexPage"]
    subpage_types: list[str] = ["Medium"]

    max_count = 1


class Medium(Page):
    parent_page_types = ["MediumIndexPage"]
    subpage_types: list[str] = []

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        context["library_items"] = get_library_items_for_facet(self, "item_medium")
        return context


class TimePeriodIndexPage(ChildPagesMixin, Page):
    parent_page_types = ["FacetIndexPage"]
    subpage_types: list[str] = ["TimePeriod"]

    max_count = 1


class TimePeriod(Page):
    parent_page_types = ["TimePeriodIndexPage"]
    subpage_types: list[str] = []

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        context["library_items"] = get_library_items_for_facet(self, "item_time_period")
        return context


class TopicIndexPage(ChildPagesMixin, Page):
    parent_page_types = ["FacetIndexPage"]
    subpage_types: list[str] = ["Topic"]

    max_count = 1


class Topic(Page):
    parent_page_types = ["TopicIndexPage"]
    subpage_types: list[str] = []

    def get_context(self, request, *args, **kwargs):
        # Avoid circular import
        from library.models import LibraryItem

        context = super().get_context(request, *args, **kwargs)

        # Get live library items matching topic, ordered by publication date
        context["library_items"] = (
            LibraryItem.objects.live()
            .filter(topics__topic=self)
            .order_by("-publication_date")
            .prefetch_related("authors__author")
        )

        return context
