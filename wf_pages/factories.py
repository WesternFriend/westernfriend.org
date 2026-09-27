from typing import Any

import factory

from common.fake_content import TOPICS, fake, headline, stream_body
from home.factories import HomePageFactory
from home.models import HomePage

from .models import (
    MollyWingateBlogIndexPage,
    MollyWingateBlogPage,
    WfPage,
    WfPageCollection,
    WfPageCollectionIndexPage,
)


def _home_page() -> HomePage:
    return HomePage.objects.first() or HomePageFactory.create()


class WfPageFactory(
    factory.django.DjangoModelFactory,
):
    class Meta:
        model = WfPage

    class Params:
        # Pools the seeder passes in so bodies can show images and link
        # to other pages; tests leave them empty.
        body_images = None
        body_links = None

    title = factory.LazyFunction(headline)  # type: ignore
    body = factory.LazyAttribute(  # type: ignore
        lambda obj: stream_body(
            images=obj.body_images,
            link_pages=obj.body_links,
            sections=3,
        ),
    )

    @classmethod
    def _create(
        cls,
        model_class: type[WfPage],
        *args: Any,
        **kwargs: Any,
    ) -> WfPage:
        instance = model_class(*args, **kwargs)  # type: ignore
        _home_page().add_child(instance=instance)
        return instance


class MollyWingateBlogIndexPageFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = MollyWingateBlogIndexPage

    title = factory.Sequence(lambda n: f"Molly Wingate Blog {n}")  # type: ignore

    @classmethod
    def _create(
        cls,
        model_class: type[MollyWingateBlogIndexPage],
        *args: Any,
        **kwargs: Any,
    ) -> MollyWingateBlogIndexPage:
        instance = model_class(*args, **kwargs)  # type: ignore
        _home_page().add_child(instance=instance)
        return instance


class MollyWingateBlogPageFactory(WfPageFactory):
    class Meta:
        model = MollyWingateBlogPage

    title = factory.LazyFunction(headline)  # type: ignore
    publication_date = factory.Faker("date_between", start_date="-3y")  # type: ignore

    @classmethod
    def _create(
        cls,
        model_class: type[MollyWingateBlogPage],
        *args: Any,
        **kwargs: Any,
    ) -> MollyWingateBlogPage:
        instance = model_class(*args, **kwargs)  # type: ignore
        parent = (
            MollyWingateBlogIndexPage.objects.first()
            or MollyWingateBlogIndexPageFactory.create()
        )
        parent.add_child(instance=instance)
        return instance


class WfPageCollectionIndexPageFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = WfPageCollectionIndexPage

    title = factory.Sequence(lambda n: f"Collections {n}")  # type: ignore

    @classmethod
    def _create(
        cls,
        model_class: type[WfPageCollectionIndexPage],
        *args: Any,
        **kwargs: Any,
    ) -> WfPageCollectionIndexPage:
        instance = model_class(*args, **kwargs)  # type: ignore
        _home_page().add_child(instance=instance)
        return instance


class WfPageCollectionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = WfPageCollection

    title = factory.LazyFunction(lambda: f"{fake.random_element(TOPICS)} Resources")  # type: ignore

    @classmethod
    def _create(
        cls,
        model_class: type[WfPageCollection],
        *args: Any,
        **kwargs: Any,
    ) -> WfPageCollection:
        instance = model_class(*args, **kwargs)  # type: ignore
        parent = (
            WfPageCollectionIndexPage.objects.first()
            or WfPageCollectionIndexPageFactory.create()
        )
        parent.add_child(instance=instance)
        return instance
