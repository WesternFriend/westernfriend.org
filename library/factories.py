import factory
from .models import (
    LibraryItem,
    LibraryItemAuthor,
)


class LibraryItemFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = LibraryItem

    title = factory.Faker("text", max_nb_chars=10)  # type: ignore
    publication_date = factory.Faker("date")  # type: ignore
    publication_date_is_approximate = factory.Faker("boolean")  # type: ignore
    # TODO: body should consist of a list of StreamField blocks
    # or just an empty list for now
    # body = factory.Faker("pylist", nb_elements=0)  # type: ignore

    # TODO: determine why the lazy facet attributes are not working
    # goal: randomly assign a facet to each library item
    # item_audience = factory.LazyAttribute(lambda _: Audience.objects.order_by("?").first())  # type: ignore # noqa: E501
    # item_genre = factory.LazyAttribute(lambda _: Genre.objects.order_by("?").first())  # type: ignore # noqa: E501
    # item_medium = factory.LazyAttribute(lambda _: Medium.objects.order_by("?").first())  # type: ignore # noqa: E501
    # item_time_period = factory.LazyAttribute(lambda _: TimePeriod.objects.order_by("?").first())  # type: ignore # noqa: E501


class LibraryItemAuthorFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = LibraryItemAuthor

    library_item = factory.RelatedFactory(LibraryItemFactory)  # type: ignore
    author = factory.RelatedFactory("contacts.factories.PersonFactory")  # type: ignore
