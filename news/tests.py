from datetime import datetime
from django.test import RequestFactory, TestCase
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


class TestNewsIndexPageGetContext(TestCase):
    def setUp(self) -> None:
        self.factory = RequestFactory()

        # Get the current year
        self.current_year = datetime.now().year

        # Get or Create a NewsIndexPage
        self.news_index_page = NewsIndexPageFactory.create()

        # Use factory to create some NewsItem instances
        self.news_items = [
            NewsItemFactory.create(publication_date=f"{year}-01-01")
            for year in range(2018, self.current_year + 1)
        ]

    def test_get_context(self) -> None:
        request = self.factory.get("/")
        context = self.news_index_page.get_context(request)

        # Test if the response has a context
        self.assertIsNotNone(context)

        # Test if the context contains the correct years
        self.assertEqual(
            list(context["news_years"]),
            list(range(2018, self.current_year + 1)),
        )

        # Test if the context contains the correct selected year
        self.assertEqual(context["selected_year"], self.current_year)

        # Test if the context contains the news_items from the selected year
        self.assertEqual(
            list(context["news_items"]),
            list(NewsItem.objects.filter(publication_date__year=self.current_year)),
        )
