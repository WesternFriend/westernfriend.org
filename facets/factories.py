import factory
from .models import (
    Audience,
    Genre,
    Medium,
    TimePeriod,
    Topic,
)


class AudienceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Audience

    title = factory.Faker("text", max_nb_chars=10)  # type: ignore


class GenreFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Genre

    title = factory.Faker("text", max_nb_chars=10)  # type: ignore


class MediumFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Medium

    title = factory.Faker("text", max_nb_chars=10)  # type: ignore


class TimePeriodFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = TimePeriod

    title = factory.Faker("text", max_nb_chars=10)  # type: ignore


class TopicFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Topic

    title = factory.Faker("text", max_nb_chars=10)  # type: ignore
