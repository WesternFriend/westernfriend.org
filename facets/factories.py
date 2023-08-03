from typing import Any
import factory
from library.factories import LibraryIndexPageFactory

from library.models import LibraryIndexPage
from .models import (
    Audience,
    FacetIndexPage,
    Genre,
    Medium,
    TimePeriod,
    Topic,
)


class FacetIndexPageFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = FacetIndexPage

    title = factory.Sequence(lambda n: f"Facet Index Page {n}")

    @classmethod
    def _create(
        cls,
        model_class: type[FacetIndexPage],
        *args: Any,
        **kwargs: Any,
    ) -> FacetIndexPage:
        instance = model_class(*args, **kwargs)  # type: ignore

        # Get the LibraryIndexPage instance if it exists, otherwise create one.
        library_index_page = LibraryIndexPage.objects.first()
        if library_index_page is None:
            library_index_page = LibraryIndexPageFactory()

        library_index_page.add_child(instance=instance)

        return instance


class AudienceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Audience

    title = factory.Sequence(lambda n: f"Audience {n}")


class GenreFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Genre

    title = factory.Sequence(lambda n: f"Genre {n}")


class MediumFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Medium

    title = factory.Sequence(lambda n: f"Medium {n}")


class TimePeriodFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = TimePeriod

    title = factory.Sequence(lambda n: f"Time Period {n}")


class TopicFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Topic

    title = factory.Sequence(lambda n: f"Topic {n}")
