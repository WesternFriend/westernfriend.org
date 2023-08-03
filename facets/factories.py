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

    title = factory.Sequence(lambda n: f"Audience {n}")


class GenreFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Genre

    title = factory.Sequence(lambda n: f"Genre {n}")


class MediumFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Medium

    title = factory.Sequence(lambda n: f"Medium {n}")


class TimePeriodFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = TimePeriod

    title = factory.Sequence(lambda n: f"Time Period {n}")


class TopicFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Topic

    title = factory.Sequence(lambda n: f"Topic {n}")
