from random import randint
from typing import Any
from django.utils.text import slugify
import factory
from factory.django import DjangoModelFactory
from wagtail.models import Page

from common.factories import PageFactory
from community.factories import CommunityPageFactory
from community.models import CommunityPage
from .models import (
    MeetingIndexPage,
    OrganizationIndexPage,
    Person,
    Meeting,
    Organization,
    PersonIndexPage,
)


class PersonIndexPageFactory(DjangoModelFactory):
    class Meta:
        model = PersonIndexPage

    title = factory.Faker("sentence", nb_words=4)  # type: ignore
    slug = factory.LazyAttribute(lambda obj: slugify(obj.title))  # type: ignore

    @classmethod
    def _create(
        cls: type["PersonIndexPageFactory"],
        model_class: type[Page],
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        instance = model_class(*args, **kwargs)
        parent = CommunityPage.objects.first()
        if parent:
            parent.add_child(instance=instance)
        else:
            community_page = CommunityPageFactory.create()
            community_page.add_child(instance=instance)
        return instance


class PersonFactory(PageFactory):
    class Meta:
        model = Person

    given_name: str = factory.Faker("first_name")  # type: ignore
    family_name: str = factory.Faker("last_name")  # type: ignore

    @factory.lazy_attribute  # type: ignore
    def title(self) -> str:
        return f"{self.given_name} {self.family_name}"

    @factory.lazy_attribute  # type: ignore
    def slug(self) -> str:
        random_number = randint(1, 1000)
        return f"{self.given_name}-{self.family_name}-{random_number}".lower()

    @classmethod
    def _create(
        cls: type["PersonFactory"],
        model_class: type[Page],
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        instance = model_class(*args, **kwargs)
        parent = PersonIndexPage.objects.first()
        if parent:
            parent.add_child(instance=instance)
        else:
            community_page = PersonIndexPageFactory.create()
            community_page.add_child(instance=instance)
        return instance


class MeetingIndexPageFactory(DjangoModelFactory):
    class Meta:
        model = MeetingIndexPage

    title = factory.Faker("sentence", nb_words=4)  # type: ignore
    slug = factory.LazyAttribute(lambda obj: slugify(obj.title))  # type: ignore

    @classmethod
    def _create(
        cls: type["MeetingIndexPageFactory"],
        model_class: type[Page],
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        instance = model_class(*args, **kwargs)
        parent = CommunityPage.objects.first()
        if parent:
            parent.add_child(instance=instance)
        else:
            community_page = CommunityPageFactory.create()
            community_page.add_child(instance=instance)
        return instance


class MeetingFactory(DjangoModelFactory):
    class Meta:
        model = Meeting

    title = factory.Faker("sentence", nb_words=4)  # type: ignore
    slug = factory.LazyAttribute(lambda obj: slugify(obj.title))  # type: ignore

    @classmethod
    def _create(
        cls,
        model_class: type[Meeting],
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        instance = model_class(*args, **kwargs)  # type: ignore
        parent = MeetingIndexPage.objects.first()
        if parent:
            parent.add_child(instance=instance)
        else:
            community_page = MeetingIndexPageFactory.create()
            community_page.add_child(instance=instance)
        return instance


class OrganizationIndexPageFactory(DjangoModelFactory):
    class Meta:
        model = OrganizationIndexPage

    title = factory.Faker("sentence", nb_words=4)  # type: ignore
    slug = factory.LazyAttribute(lambda obj: slugify(obj.title))  # type: ignore

    @classmethod
    def _create(
        cls: type["OrganizationIndexPageFactory"],
        model_class: type[Page],
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        instance = model_class(*args, **kwargs)
        parent = CommunityPage.objects.first()
        if parent:
            parent.add_child(instance=instance)
        else:
            community_page = CommunityPageFactory.create()
            community_page.add_child(instance=instance)
        return instance


class OrganizationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Organization

    title = factory.Faker("company")  # type: ignore
    slug = factory.LazyAttribute(lambda obj: slugify(obj.title))  # type: ignore

    @classmethod
    def _create(
        cls,
        model_class: type[Organization],
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        instance = model_class(*args, **kwargs)  # type: ignore
        parent = OrganizationIndexPage.objects.first()
        if parent:
            parent.add_child(instance=instance)
        else:
            community_page = OrganizationIndexPageFactory.create()
            community_page.add_child(instance=instance)
        return instance
