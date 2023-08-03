from typing import Any
from django.utils.text import slugify
import factory
from factory.django import DjangoModelFactory

from community.models import CommunityPage, OnlineWorshipIndexPage, OnlineWorship
from home.factories import HomePageFactory
from home.models import HomePage


class CommunityPageFactory(DjangoModelFactory):
    class Meta:
        model = CommunityPage

    title = factory.Faker("sentence", nb_words=4)  # type: ignore
    slug = factory.LazyAttribute(lambda obj: slugify(obj.title))  # type: ignore

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


class OnlineWorshipIndexPageFactory(DjangoModelFactory):
    class Meta:
        model = OnlineWorshipIndexPage

    title = factory.Faker("sentence", nb_words=4)  # type: ignore
    slug = factory.LazyAttribute(lambda obj: slugify(obj.title))  # type: ignore

    @classmethod
    def _create(
        cls,
        model_class: type[OnlineWorshipIndexPage],
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        instance = model_class(*args, **kwargs)  # type: ignore
        parent = CommunityPage.objects.first()
        if parent:
            parent.add_child(instance=instance)
        else:
            community_page = CommunityPageFactory.create()
            community_page.add_child(instance=instance)
        return instance


class OnlineWorshipFactory(DjangoModelFactory):
    class Meta:
        model = OnlineWorship

    title = factory.Faker("sentence", nb_words=4)  # type: ignore
    slug = factory.LazyAttribute(lambda obj: slugify(obj.title))  # type: ignore

    @classmethod
    def _create(
        cls,
        model_class: type[OnlineWorship],
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        instance = model_class(*args, **kwargs)  # type: ignore
        parent = OnlineWorshipIndexPage.objects.first()
        if parent:
            parent.add_child(instance=instance)
        else:
            online_worship_index_page = OnlineWorshipIndexPageFactory.create()
            online_worship_index_page.add_child(instance=instance)
        return instance
