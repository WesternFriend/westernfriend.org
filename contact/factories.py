import factory
from .models import (
    Person,
    Meeting,
    Organization,
)


class PersonFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Person

    given_name: str = factory.Faker("first_name")  # type: ignore
    family_name: str = factory.Faker("last_name")  # type: ignore

    @factory.lazy_attribute  # type: ignore
    def title(self) -> str:
        return f"{self.given_name} {self.family_name}"

    @factory.lazy_attribute  # type: ignore
    def slug(self) -> str:
        return f"{self.given_name}-{self.family_name}".lower()


class MeetingFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Meeting

    title = factory.Faker("company")  # type: ignore


class OrganizationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Organization

    title = factory.Faker("company")  # type: ignore
