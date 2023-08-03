from django.test import TestCase
from home.models import HomePage

from news.models import (
    NewsIndexPage,
    NewsItem,
    NewsTopic,
    NewsTopicIndexPage,
    NewsType,
    NewsTypeIndexPage,
)
from .factories import (
    NewsIndexPageFactory,
    NewsTopicIndexPageFactory,
    NewsTopicFactory,
    NewsTypeIndexPageFactory,
    NewsTypeFactory,
    NewsItemFactory,
)


class TestNewsIndexPage(TestCase):
    def test_news_index_page_creation(self) -> None:
        """Test that a NewsIndexPage can be created."""
        news_index_page = NewsIndexPageFactory.create()

        self.assertIsInstance(
            news_index_page,
            NewsIndexPage,
        )

        self.assertIsInstance(
            news_index_page.get_parent().specific,
            HomePage,
        )


class TestNewsTopicIndexPage(TestCase):
    def test_news_topic_index_page_creation(self) -> None:
        """Test that a NewsTopicIndexPage can be created."""
        news_topic_index_page = NewsTopicIndexPageFactory.create()

        self.assertIsInstance(
            news_topic_index_page,
            NewsTopicIndexPage,
        )

        self.assertIsInstance(
            news_topic_index_page.get_parent().specific,
            NewsIndexPage,
        )


class TestNewsTopic(TestCase):
    def test_news_topic_creation(self) -> None:
        """Test that a NewsTopic can be created."""
        news_topic = NewsTopicFactory.create()

        self.assertIsInstance(
            news_topic,
            NewsTopic,
        )

        self.assertIsInstance(
            news_topic.get_parent().specific,
            NewsTopicIndexPage,
        )


class TestNewsTypeIndexPage(TestCase):
    def test_news_type_index_page_creation(self) -> None:
        """Test that a NewsTypeIndexPage can be created."""
        news_type_index_page = NewsTypeIndexPageFactory.create()

        self.assertIsInstance(
            news_type_index_page,
            NewsTypeIndexPage,
        )

        self.assertIsInstance(
            news_type_index_page.get_parent().specific,
            NewsIndexPage,
        )


class TestNewsType(TestCase):
    def test_news_type_creation(self) -> None:
        """Test that a NewsType can be created."""
        news_type = NewsTypeFactory.create()

        self.assertIsInstance(
            news_type,
            NewsType,
        )

        self.assertIsInstance(
            news_type.get_parent().specific,
            NewsTypeIndexPage,
        )


class TestNewsItem(TestCase):
    def test_news_item_creation(self) -> None:
        """Test that a NewsItem can be created."""
        news_item = NewsItemFactory.create()

        self.assertIsInstance(
            news_item,
            NewsItem,
        )

        self.assertIsInstance(
            news_item.get_parent().specific,
            NewsIndexPage,
        )
