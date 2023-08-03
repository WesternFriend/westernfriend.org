from typing import Any
from django.utils.text import slugify
import factory

from home.factories import HomePageFactory
from home.models import HomePage
from .models import (
    LibraryIndexPage,
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


class LibraryIndexPageFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = LibraryIndexPage

    title = factory.Faker("sentence", nb_words=4)  # type: ignore
    slug = factory.LazyAttribute(lambda obj: slugify(obj.title))  # type: ignore
    intro = factory.Faker("text")  # type: ignore

    @classmethod
    def _create(
        cls,
        model_class: type[LibraryIndexPage],
        *args: Any,
        **kwargs: Any,
    ) -> LibraryIndexPage:
        instance = model_class(*args, **kwargs)  # type: ignore

        # Get the HomePage instance if it exists, otherwise create one.
        home_page = HomePage.objects.first()
        if home_page is None:
            home_page = HomePageFactory.create()

        # Add the instance as a child of HomePage
        home_page.add_child(instance=instance)

        return instance
