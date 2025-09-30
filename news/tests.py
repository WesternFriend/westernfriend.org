from datetime import datetime
from django.test import RequestFactory, TestCase
from home.models import HomePage

from news.models import (
    NewsIndexPage,
    NewsItem,
)
from .factories import (
    NewsIndexPageFactory,
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
        self.current_year = datetime.now().year
        self.news_index_page = NewsIndexPageFactory.create()

        # Create NewsItem instances with associated NewsItemTopics
        self.news_items = []
        self.current_year_news_topics = []
        self.current_year_news_items = []
        self.initial_year = 2018

        for year in range(2018, self.current_year + 1):
            # Create a NewsItem for each year
            news_item = NewsItemFactory.create(
                publication_date=f"{year}-01-01",
                parent=self.news_index_page,
            )
            self.news_items.append(news_item)

            # Add the current year's news item and topic to their respective lists
            if year == self.current_year:
                self.current_year_news_items.append(news_item)

    def test_get_context(self) -> None:
        request = self.factory.get("/")
        context = self.news_index_page.get_context(request)

        # Test if the response has a context
        self.assertIsNotNone(context)

        # Test if the context contains the correct years
        self.assertEqual(
            list(context["news_years"]),
            list(range(self.initial_year, self.current_year + 1)),
        )

        # Test if the context contains the correct selected year
        self.assertEqual(context["selected_year"], self.current_year)

        # assert grouped_news_items is a defaultdict
        self.assertIsInstance(context["grouped_news_items"], dict)

        # Extract topic titles from NewsItemTopic instances
        expected_topics = []
        for item in self.current_year_news_items:
            for topic in item.topics.all():
                expected_topics.append(topic.topic.title)

        # Extract topic titles from the context's grouped_news_items keys
        actual_topics = sorted(list(context["grouped_news_items"].keys()))

        # Test if grouped_news_items has the correct keys
        self.assertEqual(actual_topics, expected_topics)
