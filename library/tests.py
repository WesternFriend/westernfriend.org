from django.test import SimpleTestCase

from library.helpers import create_querystring_from_facets


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
