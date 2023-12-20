import factory
from typing import Any
from wagtail_factories import PageFactory
from home.factories import HomePageFactory

from home.models import HomePage

from .models import (
    NewsIndexPage,
    NewsTypeIndexPage,
    NewsType,
    NewsItem,
)


class NewsIndexPageFactory(PageFactory):
    class Meta:
        model = NewsIndexPage

    title = factory.Sequence(lambda n: f"News Index Page {n}")
    intro = "News index page"

    @classmethod
    def _create(
        cls,
        model_class: type[NewsIndexPage],
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        kwargs.pop("parent", None)
        instance = model_class(*args, **kwargs)  # type: ignore
        parent = HomePage.objects.first()
        if parent:
            parent.add_child(instance=instance)
        else:
            online_worship_index_page = HomePageFactory.create()
            online_worship_index_page.add_child(instance=instance)
        return instance


class NewsTypeIndexPageFactory(PageFactory):
    class Meta:
        model = NewsTypeIndexPage

    title = factory.Sequence(lambda n: f"News type index {n}")
    intro = "News type index page"

    @classmethod
    def _create(
        cls,
        model_class: type[NewsTypeIndexPage],
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        kwargs.pop("parent", None)
        instance = model_class(*args, **kwargs)  # type: ignore

        parent = NewsIndexPage.objects.first()
        if parent:
            parent.add_child(instance=instance)
        else:
            news_index_page = NewsIndexPageFactory.create()
            news_index_page.add_child(instance=instance)
        return instance


class NewsTypeFactory(PageFactory):
    class Meta:
        model = NewsType

    title = factory.Sequence(lambda n: f"News type {n}")
    intro = "News type page"

    @classmethod
    def _create(
        cls,
        model_class: type[NewsType],
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        kwargs.pop("parent", None)
        instance = model_class(*args, **kwargs)  # type: ignore

        parent = NewsTypeIndexPage.objects.first()
        if parent:
            parent.add_child(instance=instance)
        else:
            news_type_index_page = NewsTypeIndexPageFactory.create()
            news_type_index_page.add_child(instance=instance)
        return instance


class NewsItemFactory(PageFactory):
    class Meta:
        model = NewsItem

    title = factory.Sequence(lambda n: f"News item {n}")

    @classmethod
    def _create(
        cls,
        model_class: type[NewsItem],
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        kwargs.pop("parent", None)
        instance = model_class(*args, **kwargs)  # type: ignore

        parent = NewsIndexPage.objects.first()
        if parent:
            parent.add_child(instance=instance)
        else:
            news_type = NewsIndexPageFactory.create()
            news_type.add_child(instance=instance)
        return instance
