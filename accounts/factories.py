from django.contrib.auth import get_user_model

import factory
from factory.django import DjangoModelFactory


class UserFactory(DjangoModelFactory):
    class Meta:
        model = get_user_model()

    email = factory.Sequence(lambda n: f"user{n}@westernfriend.org")
    is_staff = factory.Faker("pybool")
    is_active = factory.Faker("pybool")
