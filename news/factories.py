import factory
from typing import Any
from wagtail_factories import PageFactory
from home.factories import HomePageFactory

from home.models import HomePage

from .models import (
    NewsIndexPage,
    NewsItem,
    NewsItemTopic,
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


class NewsItemTopicFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = NewsItemTopic

    news_item = None  # Don't create a NewsItem by default
    topic = factory.SubFactory("facets.factories.TopicFactory")


class NewsItemFactory(PageFactory):
    class Meta:
        model = NewsItem

    title = factory.Sequence(lambda n: f"News item {n}")
    live = True

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

    @factory.post_generation
    def create_news_item_topic(self, create, extracted, **kwargs):
        """Create a NewsItemTopic for the NewsItem."""
        if not create or "news_item" in kwargs:
            # Avoid recursion if 'news_item' is in kwargs
            return

        if extracted:
            # A list of topics were provided, use them
            for topic in extracted:
                NewsItemTopicFactory(news_item=self, topic=topic)
        else:
            # No specific topics provided, create a default one
            NewsItemTopicFactory(news_item=self)
