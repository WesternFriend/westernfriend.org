from typing import Any

import factory
from wagtail_factories import PageFactory

from common.fake_content import fake, headline, stream_body
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

    class Params:
        # Pools the seeder passes in so bodies can show images and link
        # to other pages; tests leave them empty.
        body_images = None
        body_links = None

    title = factory.LazyFunction(headline)  # type: ignore
    slug = factory.Sequence(lambda n: f"news-item-{n}")  # type: ignore
    teaser = factory.LazyFunction(lambda: fake.sentence(nb_words=12)[:100])  # type: ignore
    publication_date = factory.Faker("date_between", start_date="-2y")  # type: ignore
    body = factory.LazyAttribute(  # type: ignore
        lambda obj: stream_body(
            images=obj.body_images,
            link_pages=obj.body_links,
            sections=2,
        ),
    )
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
