from typing import Any
import factory
from factory.django import DjangoModelFactory
from wagtail.rich_text import RichText

from home.factories import HomePageFactory
from home.models import HomePage
from .models import Product, StoreIndexPage, ProductIndexPage


class StoreIndexPageFactory(DjangoModelFactory):
    class Meta:
        model = StoreIndexPage

    title = factory.Sequence(lambda n: f"Store Index Page {n}")
    intro = RichText("Store Index Page intro")

    @classmethod
    def _create(
        cls,
        model_class: type[StoreIndexPage],
        *args: Any,
        **kwargs: Any,
    ) -> StoreIndexPage:
        instance = model_class(*args, **kwargs)  # type: ignore

        # Get the HomePage instance if it exists, otherwise create one.
        home_page = HomePage.objects.first()
        if home_page is None:
            home_page = HomePageFactory()

        home_page.add_child(instance=instance)

        return instance


class ProductIndexPageFactory(DjangoModelFactory):
    class Meta:
        model = ProductIndexPage

    title = factory.Sequence(lambda n: f"Product Index Page {n}")

    @classmethod
    def _create(
        cls,
        model_class: type[ProductIndexPage],
        *args: Any,
        **kwargs: Any,
    ) -> ProductIndexPage:
        instance = model_class(*args, **kwargs)  # type: ignore

        # Get the StoreIndexPage instance if it exists, otherwise create one.
        store_index_page = StoreIndexPage.objects.first()
        if store_index_page is None:
            store_index_page = StoreIndexPageFactory()

        store_index_page.add_child(instance=instance)

        return instance


class ProductFactory(DjangoModelFactory):
    class Meta:
        model = Product

    title = factory.Sequence(lambda n: f"Product {n}")
    description = RichText("Product description")
    price_usd = factory.Faker(  # type: ignore
        "pydecimal",
        left_digits=2,
        right_digits=2,
        positive=True,
    )
    available = factory.Iterator([True, False])  # type: ignore

    # TODO: add a MockWagtailImage class
    # and use it here
    # image = factory.LazyAttribute(lambda _: get_test_image_file())

    @classmethod
    def _create(
        cls,
        model_class: type[Product],
        *args: Any,
        **kwargs: Any,
    ) -> Product:
        instance = model_class(*args, **kwargs)

        # Get the ProductIndexPage instance if it exists, otherwise create one.
        product_index_page = ProductIndexPage.objects.first()
        if product_index_page is None:
            product_index_page = ProductIndexPageFactory()

        product_index_page.add_child(instance=instance)

        return instance
