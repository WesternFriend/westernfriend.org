import factory
from factory.django import DjangoModelFactory
from factory.fuzzy import FuzzyInteger, FuzzyDate, FuzzyChoice
from django.utils.timezone import now, timedelta
from subscription.models import (
    MagazineFormatChoices,
    MagazinePriceGroupChoices,
    Subscription,
)

from accounts.factories import UserFactory


class SubscriptionFactory(DjangoModelFactory):
    class Meta:
        model = Subscription

    magazine_format = FuzzyChoice(MagazineFormatChoices.values)
    price_group = FuzzyChoice(MagazinePriceGroupChoices.values)
    price = FuzzyInteger(0, 100)
    recurring = factory.Faker("pybool")
    start_date = FuzzyDate(
        start_date=now().date() - timedelta(days=365),
        end_date=now().date(),
    )
    end_date = FuzzyDate(
        start_date=now().date(),
        end_date=now().date() + timedelta(days=365),
    )
    subscriber_given_name = factory.Faker("first_name")
    subscriber_family_name = factory.Faker("last_name")
    subscriber_organization = factory.Faker("company")
    subscriber_street_address = factory.Faker("street_address")
    subscriber_street_address_line_2 = factory.Faker("secondary_address")
    subscriber_postal_code = factory.Faker("postcode")
    subscriber_address_locality = factory.Faker("city")
    subscriber_address_region = factory.Faker("state")
    subscriber_address_country = factory.Faker("country")

    user = factory.SubFactory(UserFactory)
    paid = factory.Faker("pybool")

    braintree_subscription_id = factory.Sequence(
        lambda n: f"braintree_subscription_id_{n}",
    )
