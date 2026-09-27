from typing import Any

import factory
from django.utils.text import slugify
from factory.django import DjangoModelFactory

from common.fake_content import paragraphs
from community.factories import CommunityPageFactory
from community.models import CommunityPage
from contact.factories import MeetingFactory, PersonFactory
from memorials.models import Memorial, MemorialIndexPage


class MemorialIndexPageFactory(DjangoModelFactory):
    class Meta:
        model = MemorialIndexPage

    title = factory.Faker("sentence", nb_words=4)  # type: ignore
    slug = factory.LazyAttribute(lambda obj: slugify(obj.title))  # type: ignore

    @classmethod
    def _create(
        cls,
        model_class: type[MemorialIndexPage],
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        instance = model_class(*args, **kwargs)  # type: ignore
        parent = CommunityPage.objects.first()
        if parent:
            parent.add_child(instance=instance)
        else:
            home_page = CommunityPageFactory.create()
            home_page.add_child(instance=instance)
        return instance


class MemorialFactory(DjangoModelFactory):
    class Meta:
        model = Memorial

    memorial_person = factory.SubFactory(PersonFactory)  # type: ignore
    date_of_birth = factory.Faker("date_between", start_date="-100y", end_date="-60y")  # type: ignore
    date_of_death = factory.Faker("date_between", start_date="-10y", end_date="-30d")  # type: ignore
    dates_are_approximate = factory.Faker("boolean", chance_of_getting_true=15)  # type: ignore
    memorial_minute = factory.LazyFunction(lambda: paragraphs(3))  # type: ignore
    memorial_meeting = factory.SubFactory(MeetingFactory)  # type: ignore

    slug = factory.LazyAttribute(lambda obj: slugify(obj.title))  # type: ignore

    @factory.lazy_attribute  # type: ignore
    def title(self) -> str:
        return f"{self.memorial_person.given_name} {self.memorial_person.family_name}"

    @classmethod
    def _create(
        cls,
        model_class: type[Memorial],
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        instance = model_class(*args, **kwargs)  # type: ignore
        parent = MemorialIndexPage.objects.first()
        if parent:
            parent.add_child(instance=instance)
        else:
            home_page = MemorialIndexPageFactory.create()
            home_page.add_child(instance=instance)
        return instance
