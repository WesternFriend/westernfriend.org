import json
import re
from datetime import date

from django.test import RequestFactory, TestCase
from django.utils import timezone
from wagtail.models import Site

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
        self.current_year = timezone.localdate().year
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
        expected_topics = [
            topic.topic.title
            for item in self.current_year_news_items
            for topic in item.topics.all()
        ]

        # Extract topic titles from the context's grouped_news_items keys
        actual_topics = sorted(context["grouped_news_items"].keys())

        # Test if grouped_news_items has the correct keys
        self.assertEqual(actual_topics, expected_topics)


class TestNewsItemStructuredData(TestCase):
    def setUp(self) -> None:
        # Serve the factory-built page tree from the default site. Clear
        # Wagtail's cached site root paths on cleanup, because the cache
        # outlives this test's transaction rollback.
        self.news_item = NewsItemFactory.create(
            title="Yearly Meeting gathers",
            publication_date=date(2024, 7, 1),
            teaser='Friends met in "Berkeley".\nAll were welcome.',
        )
        Site.objects.update(root_page=HomePage.objects.get())
        Site.clear_site_root_paths_cache()
        self.addCleanup(Site.clear_site_root_paths_cache)

    def get_news_article_json_ld(self) -> dict:
        response = self.client.get(self.news_item.url)
        self.assertEqual(response.status_code, 200)
        json_ld_blocks = [
            json.loads(block)
            for block in re.findall(
                r'<script type="application/ld\+json">(.*?)</script>',
                response.content.decode(),
                re.DOTALL,
            )
        ]
        return next(
            block for block in json_ld_blocks if block["@type"] == "NewsArticle"
        )

    def test_renders_valid_json_ld_without_tags(self) -> None:
        """Test that the JSON-LD stays valid when optional fields are absent."""
        data = self.get_news_article_json_ld()

        self.assertEqual(data["headline"], "Yearly Meeting gathers")
        self.assertEqual(data["datePublished"], "2024-07-01")
        self.assertEqual(
            data["description"],
            'Friends met in "Berkeley".\nAll were welcome.',
        )
        self.assertEqual(data["publisher"]["name"], "Western Friend")
        self.assertNotIn("keywords", data)

    def test_renders_tags_as_keywords(self) -> None:
        """Test that page tags appear as JSON-LD keywords."""
        self.news_item.tags.add("quakers", "peace")
        self.news_item.save()

        data = self.get_news_article_json_ld()

        self.assertCountEqual(data["keywords"], ["quakers", "peace"])
