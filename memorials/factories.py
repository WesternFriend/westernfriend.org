from typing import Any
from django.utils.text import slugify
import factory
from factory.django import DjangoModelFactory
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
    date_of_birth = "1950-01-01"
    date_of_death = "2000-01-01"
    dates_are_approximate = False
    memorial_minute = "Test Minute"
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
