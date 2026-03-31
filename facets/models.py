from wagtail.models import Page


class FacetIndexPage(Page):
    parent_page_types = ["library.LibraryIndexPage"]
    subpage_types: list[str] = [
        "AudienceIndexPage",
        "GenreIndexPage",
        "MediumIndexPage",
        "TimePeriodIndexPage",
        "TopicIndexPage",
    ]

    max_count = 1


class AudienceIndexPage(Page):
    parent_page_types = ["FacetIndexPage"]
    subpage_types: list[str] = ["Audience"]

    max_count = 1


class Audience(Page):
    parent_page_types = ["AudienceIndexPage"]
    subpage_types: list[str] = []

    def get_context(self, request, *args, **kwargs):
        # Avoid circular import
        from library.models import LibraryItem

        context = super().get_context(request, *args, **kwargs)

        # Get live library items matching audience
        context["library_items"] = (
            LibraryItem.objects.live()
            .filter(item_audience=self)
            .prefetch_related("authors__author")
        )

        return context


class GenreIndexPage(Page):
    parent_page_types = ["FacetIndexPage"]
    subpage_types: list[str] = ["Genre"]

    max_count = 1


class Genre(Page):
    parent_page_types = ["GenreIndexPage"]
    subpage_types: list[str] = []

    def get_context(self, request, *args, **kwargs):
        # Avoid circular import
        from library.models import LibraryItem

        context = super().get_context(request, *args, **kwargs)

        # Get live library items matching genre
        context["library_items"] = (
            LibraryItem.objects.live()
            .filter(item_genre=self)
            .prefetch_related("authors__author")
        )

        return context


class MediumIndexPage(Page):
    parent_page_types = ["FacetIndexPage"]
    subpage_types: list[str] = ["Medium"]

    max_count = 1


class Medium(Page):
    parent_page_types = ["MediumIndexPage"]
    subpage_types: list[str] = []

    def get_context(self, request, *args, **kwargs):
        # Avoid circular import
        from library.models import LibraryItem

        context = super().get_context(request, *args, **kwargs)

        # Get live library items matching medium
        context["library_items"] = (
            LibraryItem.objects.live()
            .filter(item_medium=self)
            .prefetch_related("authors__author")
        )

        return context


class TimePeriodIndexPage(Page):
    parent_page_types = ["FacetIndexPage"]
    subpage_types: list[str] = ["TimePeriod"]

    max_count = 1


class TimePeriod(Page):
    parent_page_types = ["TimePeriodIndexPage"]
    subpage_types: list[str] = []

    def get_context(self, request, *args, **kwargs):
        # Avoid circular import
        from library.models import LibraryItem

        context = super().get_context(request, *args, **kwargs)

        # Get live library items matching time period
        context["library_items"] = (
            LibraryItem.objects.live()
            .filter(item_time_period=self)
            .prefetch_related("authors__author")
        )

        return context


class TopicIndexPage(Page):
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

        # Get live library items matching topic
        context["library_items"] = (
            LibraryItem.objects.live()
            .filter(topics__topic=self)
            .prefetch_related("authors__author")
        )

        return context
