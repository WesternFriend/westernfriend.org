from decimal import Decimal
import factory
from factory.django import DjangoModelFactory
from faker import Faker
from .models import (
    Order,
    OrderItem,
)

fake = Faker()


class OrderFactory(DjangoModelFactory):
    class Meta:
        model = Order

    purchaser_given_name: str = factory.Faker("first_name")  # type: ignore
    purchaser_family_name: str = factory.Faker("last_name")  # type: ignore
    purchaser_meeting_or_organization: str = factory.Faker("company")  # type: ignore
    purchaser_email: str = factory.Faker("email")  # type: ignore
    recipient_name: str = factory.LazyAttribute(  # type: ignore
        lambda x: f"{fake.first_name()} {fake.last_name()}",  # type: ignore
    )
    recipient_street_address: str = factory.Faker("street_address")  # type: ignore
    recipient_postal_code: str = factory.Faker("zipcode")  # type: ignore
    recipient_po_box_number: str = factory.Faker("random_int")  # type: ignore
    recipient_address_locality: str = factory.Faker("city")  # type: ignore
    recipient_address_region: str = factory.Faker("state")  # type: ignore
    recipient_address_country: str = factory.Faker("country")  # type: ignore
    shipping_cost: Decimal = factory.Faker(  # type: ignore
        "pydecimal",
        left_digits=2,
        right_digits=2,
        positive=True,
    )
    paid: bool = factory.Faker("boolean")  # type: ignore


class OrderItemFactory(DjangoModelFactory):
    class Meta:
        model = OrderItem

    order: Order = factory.SubFactory(OrderFactory)  # type: ignore
    product_title: str = factory.Faker(  # type: ignore
        "sentence",
        nb_words=3,
    )
    product_id: int = factory.Faker(  # type: ignore
        "random_int",
        min=1,
        max=99999,
    )
    price: Decimal = factory.Faker(  # type: ignore
        "pydecimal",
        left_digits=2,
        right_digits=2,
        positive=True,
    )
    quantity: int = factory.Faker(  # type: ignore
        "random_int",
        min=1,
        max=100,
    )
