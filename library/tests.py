import random
from unittest.mock import Mock, patch
from django.test import RequestFactory, SimpleTestCase, TestCase
from facets.factories import (
    AudienceFactory,
    GenreFactory,
    MediumFactory,
    TimePeriodFactory,
    TopicFactory,
)
from home.models import HomePage

from library.models import LibraryIndexPage

from .factories import (
    LibraryIndexPageFactory,
    LibraryItemFactory,
)

from library.helpers import (
    QUERYSTRING_FACETS,
    create_querystring_from_facets,
    filter_querystring_facets,
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
        query = {key: "value" for key in QUERYSTRING_FACETS}
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
