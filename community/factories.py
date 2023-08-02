from typing import Any
from django.utils.text import slugify
import factory
from factory.django import DjangoModelFactory
from wagtail.models import Page

from community.models import CommunityPage
from home.factories import HomePageFactory
from home.models import HomePage


class CommunityPageFactory(DjangoModelFactory):
    class Meta:
        model = CommunityPage

    title = factory.Faker("sentence", nb_words=4)  # type: ignore
    slug = factory.LazyAttribute(lambda obj: slugify(obj.title))  # type: ignore
    depth = factory.Sequence(lambda n: n + 3)  # Assumes that HomePage page depth is 1

    @factory.lazy_attribute  # type: ignore
    def path(self):
        root_path = Page.get_first_root_node().path
        return f"{root_path}{str(self.depth).zfill(4)}"

    @classmethod
    def _create(
        cls,
        model_class: type[CommunityPage],
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        instance = model_class(*args, **kwargs)  # type: ignore
        parent = HomePage.objects.first()
        if parent:
            parent.add_child(instance=instance)
        else:
            home_page = HomePageFactory.create()
            home_page.add_child(instance=instance)
        return instance
