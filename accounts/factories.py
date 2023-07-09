from django.contrib.auth import get_user_model

import factory
from factory.django import DjangoModelFactory


class UserFactory(DjangoModelFactory):
    class Meta:
        model = get_user_model()

    email = factory.Faker("email")
    is_staff = factory.Faker("pybool")
    is_active = factory.Faker("pybool")
