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

    purchaser_given_name = factory.Faker("first_name")
    purchaser_family_name = factory.Faker("last_name")
    purchaser_meeting_or_organization = factory.Faker("company")
    purchaser_email = factory.Faker("email")
    recipient_name = factory.LazyAttribute(
        lambda x: f"{fake.first_name()} {fake.last_name()}",
    )
    recipient_street_address = factory.Faker("street_address")
    recipient_postal_code = factory.Faker("zipcode")
    recipient_po_box_number = factory.Faker("random_int")
    recipient_address_locality = factory.Faker("city")
    recipient_address_region = factory.Faker("state")
    recipient_address_country = factory.Faker("country")
    shipping_cost = factory.Faker(
        "pydecimal",
        left_digits=2,
        right_digits=2,
        positive=True,
    )
    paid = factory.Faker("boolean")


class OrderItemFactory(DjangoModelFactory):
    class Meta:
        model = OrderItem

    order = factory.SubFactory(OrderFactory)
    product_title = factory.Faker(
        "sentence",
        nb_words=3,
    )
    product_id = factory.Faker(
        "random_int",
        min=1,
        max=99999,
    )
    price = factory.Faker(
        "pydecimal",
        left_digits=2,
        right_digits=2,
        positive=True,
    )
    quantity = factory.Faker(
        "random_int",
        min=1,
        max=100,
    )
