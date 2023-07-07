import factory
from factory.django import DjangoModelFactory
from wagtail.rich_text import RichText
from .models import Product


class ProductFactory(DjangoModelFactory):
    class Meta:
        model = Product

    title = factory.Sequence(lambda n: f"Product {n}")
    description = RichText("Product description")
    price = factory.Faker(  # type: ignore
        "pydecimal",
        left_digits=2,
        right_digits=2,
        positive=True,
    )
    available = factory.Iterator([True, False])

    # TODO: add a MockWagtailImage class
    # and use it here
    # image = factory.LazyAttribute(lambda _: get_test_image_file())
