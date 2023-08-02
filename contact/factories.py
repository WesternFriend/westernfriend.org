from typing import Any
from django.utils.text import slugify
import factory
from factory.django import DjangoModelFactory
from wagtail.models import Page

from common.factories import PageFactory
from community.factories import CommunityPageFactory
from community.models import CommunityPage
from .models import (
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
    depth = factory.Sequence(
        lambda n: n + 4,
    )  # Assumes that CommunityPage page depth is 2

    @factory.lazy_attribute  # type: ignore
    def path(self):
        # Constructs a valid path by appending self.depth
        # to the path of root page
        root_path = Page.get_first_root_node().path
        return f"{root_path}{str(self.depth).zfill(4)}"

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
    depth = factory.Sequence(
        lambda n: n + 4,
    )

    @factory.lazy_attribute  # type: ignore
    def path(self):
        # Constructs a valid path by appending self.depth
        # to the path of root page
        root_path = Page.get_first_root_node().path
        return f"{root_path}{str(self.depth).zfill(4)}"

    @factory.lazy_attribute  # type: ignore
    def title(self) -> str:
        return f"{self.given_name} {self.family_name}"

    @factory.lazy_attribute  # type: ignore
    def slug(self) -> str:
        return f"{self.given_name}-{self.family_name}".lower()

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


class MeetingFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Meeting

    title = factory.Faker("company")  # type: ignore


class OrganizationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Organization

    title = factory.Faker("company")  # type: ignore
