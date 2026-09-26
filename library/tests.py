import datetime
import json
import random
import re
from unittest.mock import Mock, patch

from django.test import RequestFactory, SimpleTestCase, TestCase
from wagtail.models import Site

from contact.factories import PersonFactory
from facets.factories import (
    AudienceFactory,
    GenreFactory,
    MediumFactory,
    TimePeriodFactory,
    TopicFactory,
)
from home.models import HomePage
from library.helpers import (
    QUERYSTRING_FACETS,
    create_querystring_from_facets,
    filter_querystring_facets,
)
from library.models import LibraryIndexPage, LibraryItemAuthor, LibraryItemTopic

from .factories import (
    LibraryIndexPageFactory,
    LibraryItemFactory,
)


class TestCreateQuerystringFromFacets(SimpleTestCase):
    def test_empty_dictionary(self) -> None:
        """Test that an empty dictionary returns an empty string."""
        facets: dict = {}
        result = create_querystring_from_facets(facets)
        self.assertEqual(result, "")

    def test_single_key_value_pair(self) -> None:
        """Test that a dictionary with a single key-value pair returns a
        correct query string."""
        facets = {"key1": "value1"}
        result = create_querystring_from_facets(facets)
        self.assertEqual(result, "key1=value1")

    def test_multiple_key_value_pairs(self) -> None:
        """Test that a dictionary with multiple key-value pairs returns a
        correct query string."""
        facets = {"key1": "value1", "key2": "value2", "key3": "value3"}
        result = create_querystring_from_facets(facets)
        # we can't predict the order of items in the dictionary,
        # so we need to parse the result and compare dictionaries
        result_dict = dict(item.split("=") for item in result.split("&"))
        self.assertDictEqual(result_dict, facets)


class TestFilterQuerystringFacets(SimpleTestCase):
    def test_empty_query(self) -> None:
        """Test that an empty query returns an empty dictionary."""
        query: dict = {}
        result = filter_querystring_facets(query)
        self.assertEqual(result, {})

    def test_query_with_no_valid_facets(self) -> None:
        """Test that a query with no valid facets returns an empty
        dictionary."""
        query = {"invalid1": "value1", "invalid2": "value2"}
        result = filter_querystring_facets(query)
        self.assertEqual(result, {})

    def test_query_with_some_valid_facets(self) -> None:
        """Test that a query with some valid facets returns a dictionary with
        only the valid facets."""
        valid_key = random.choice(QUERYSTRING_FACETS)
        query = {valid_key: "value1", "invalid": "value2"}
        result = filter_querystring_facets(query)
        expected_result = {valid_key: "value1"}
        self.assertDictEqual(result, expected_result)

    def test_query_with_all_valid_facets(self) -> None:
        """Test that a query with all valid facets returns the same
        dictionary."""
        query = dict.fromkeys(QUERYSTRING_FACETS, "value")
        result = filter_querystring_facets(query)
        self.assertDictEqual(result, query)


class TestLibraryIndexPageFactory(TestCase):
    def test_library_index_page_creation(self) -> None:
        library_index_page = LibraryIndexPageFactory.create()

        # Now test that it was created
        self.assertIsNotNone(library_index_page)
        self.assertIsInstance(
            library_index_page,
            LibraryIndexPage,
        )

        # Verify the home page is a direct child of the HomePage
        self.assertIsInstance(
            library_index_page.get_parent().specific,
            HomePage,
        )


class TestLibraryIndexPage(TestCase):
    def setUp(self) -> None:
        self.factory = RequestFactory()
        self.library_index_page = LibraryIndexPageFactory.create()
        self.library_item = LibraryItemFactory.create()

    @patch("library.models.filter_querystring_facets")
    @patch("library.models.get_paginated_items")
    @patch("library.models.create_querystring_from_facets")
    def test_get_context(
        self,
        mock_create_querystring: Mock,
        mock_get_paginated_items: Mock,
        mock_filter_querystring: Mock,
    ) -> None:
        AudienceFactory.create_batch(5)
        GenreFactory.create_batch(5)
        MediumFactory.create_batch(5)
        TimePeriodFactory.create_batch(5)
        TopicFactory.create_batch(5)

        request = self.factory.get("/")
        context = self.library_index_page.get_context(request)

        self.assertIn("audiences", context)
        self.assertIn("genres", context)
        self.assertIn("mediums", context)
        self.assertIn("time_periods", context)
        self.assertIn("topics", context)
        self.assertIn("authors", context)
        self.assertIn("paginated_items", context)
        self.assertIn("current_querystring", context)

        mock_filter_querystring.assert_called_once_with(query=request.GET.dict())
        mock_get_paginated_items.assert_called_once()
        mock_create_querystring.assert_called_once()


class TestLibraryItemGetContext(TestCase):
    def setUp(self) -> None:
        self.factory = RequestFactory()
        self.library_item = LibraryItemFactory.create()

    def test_get_context(self) -> None:
        """Test that get_context prefetches authors and topics."""
        authors = PersonFactory.create_batch(2)
        topics = TopicFactory.create_batch(2)

        for author in authors:
            LibraryItemAuthor.objects.create(
                library_item=self.library_item,
                author=author,
            )

        for topic in topics:
            LibraryItemTopic.objects.create(
                library_item=self.library_item,
                topic=topic,
            )

        request = self.factory.get("/")
        with self.assertNumQueries(4):
            context = self.library_item.get_context(request)

        self.assertIsNotNone(context)
        self.assertIsInstance(context, dict)
        self.assertIn("page", context)
        self.assertEqual(context["page"].pk, self.library_item.pk)

        with self.assertNumQueries(0):
            context_authors = [
                library_item_author.author
                for library_item_author in context["page"].authors.all()
            ]
            context_topics = [
                library_item_topic.topic
                for library_item_topic in context["page"].topics.all()
            ]

        self.assertCountEqual(
            [author.pk for author in context_authors],
            [author.pk for author in authors],
        )
        self.assertCountEqual(
            [topic.pk for topic in context_topics],
            [topic.pk for topic in topics],
        )


class TestLibraryItemStructuredData(TestCase):
    def test_renders_valid_json_ld(self) -> None:
        """Test that the library item page embeds valid schema.org JSON-LD."""
        library_item = LibraryItemFactory.create(
            title="Faith and Practice",
            publication_date=datetime.date(2020, 5, 17),
        )
        author = PersonFactory.create()
        topic = TopicFactory.create()
        LibraryItemAuthor.objects.create(library_item=library_item, author=author)
        LibraryItemTopic.objects.create(library_item=library_item, topic=topic)
        # Serve the factory-built page tree from the default site. Clear
        # Wagtail's cached site root paths on cleanup, because the cache
        # outlives this test's transaction rollback.
        Site.objects.update(root_page=HomePage.objects.get())
        Site.clear_site_root_paths_cache()
        self.addCleanup(Site.clear_site_root_paths_cache)

        response = self.client.get(library_item.url)

        self.assertEqual(response.status_code, 200)
        json_ld_blocks = [
            json.loads(block)
            for block in re.findall(
                r'<script type="application/ld\+json">(.*?)</script>',
                response.content.decode(),
                re.DOTALL,
            )
        ]
        data = next(
            block for block in json_ld_blocks if block["@type"] == "CreativeWork"
        )

        self.assertEqual(data["name"], "Faith and Practice")
        self.assertEqual(data["author"][0]["@type"], "Person")
        self.assertEqual(data["author"][0]["givenName"], author.given_name)
        self.assertEqual(data["about"], [topic.title])
        self.assertEqual(data["datePublished"], "2020-05-17")
