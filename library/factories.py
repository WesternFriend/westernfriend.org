from typing import Any

import factory
from django.utils.text import slugify

from common.fake_content import headline, stream_body
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

    class Params:
        # Pools the seeder passes in so bodies can show images and link
        # to other pages; tests leave them empty.
        body_images = None
        body_links = None

    title = factory.LazyFunction(headline)  # type: ignore
    slug = factory.Sequence(lambda n: f"library-item-{n}")  # type: ignore
    publication_date = factory.Faker("date_between", start_date="-40y")  # type: ignore
    publication_date_is_approximate = factory.Faker(  # type: ignore
        "boolean",
        chance_of_getting_true=20,
    )
    body = factory.LazyAttribute(  # type: ignore
        lambda obj: stream_body(
            images=obj.body_images,
            link_pages=obj.body_links,
            sections=2,
        ),
    )

    # TODO: determine why lazy facet attributes (factory.LazyAttribute picking a
    # random Audience, Genre, Medium, and TimePeriod) are not working
    # goal: randomly assign a facet to each library item

    @classmethod
    def _create(
        cls,
        model_class: type[LibraryItem],
        *args: Any,
        **kwargs: Any,
    ) -> LibraryItem:
        instance = model_class(*args, **kwargs)  # type: ignore

        # Get the LibraryIndexPage instance if it exists, otherwise create one.
        library_index_page = LibraryIndexPage.objects.first()
        if library_index_page is None:
            library_index_page = LibraryIndexPageFactory.create()

        # Add the instance as a child of LibraryIndexPage
        library_index_page.add_child(instance=instance)

        return instance


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
