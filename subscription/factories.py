import factory
from factory.django import DjangoModelFactory
from accounts.models import User

from subscription.models import (
    Subscription,
)

from accounts.factories import UserFactory


class SubscriptionFactory(DjangoModelFactory):
    class Meta:
        model = Subscription

    user: User = factory.SubFactory(UserFactory)  # type: ignore

    paypal_subscription_id = factory.Sequence(
        lambda n: f"paypal_subscription_id_{n}",
    )
    expiration_date = factory.Faker("future_date", end_date="+365d")  # type: ignore
