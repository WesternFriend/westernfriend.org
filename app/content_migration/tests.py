from django.test import SimpleTestCase

from bs4 import BeautifulSoup

from content_migration.management.commands.shared import (
    clean_pullquote_tags,
    extract_pullquotes,
)


class CleanPullquoteTagsSimpleTestCase(SimpleTestCase):
    def test_clean_pullquote_tags(self):
        soup_context = BeautifulSoup(
            """<p>Some text[pullquote]with a pullquote[/pullquote]</p>""",
            "html.parser",
        )  # noqa: E501
        input_bs4_tag = soup_context.find("p")
        output_bs4_tag = clean_pullquote_tags(input_bs4_tag)
        expected_bs4_tag = BeautifulSoup(
            """<p>Some textwith a pullquote</p>""", "html.parser"
        ).find("p")

        self.assertEqual(output_bs4_tag, expected_bs4_tag)

    def test_clean_pullquote_tags_with_multiple_pullquotes(self):
        soup_context = BeautifulSoup(
            """<p>Some text[pullquote]with a pullquote[/pullquote] and another [pullquote]with a pullquote[/pullquote]</p>""",  # noqa: E501
            "html.parser",
        )
        input_bs4_tag = soup_context.find("p")
        output_bs4_tag = clean_pullquote_tags(input_bs4_tag)
        expected_bs4_tag = BeautifulSoup(
            """<p>Some textwith a pullquote and another with a pullquote</p>""",
            "html.parser",
        ).find("p")

        self.assertEqual(output_bs4_tag, expected_bs4_tag)

    def test_clean_pullquote_tags_with_none_as_input(self):
        input_bs4_tag = None

        with self.assertRaises(AttributeError):
            clean_pullquote_tags(input_bs4_tag)


class ExtractPullquotesSimpleTestCase(SimpleTestCase):
    def test_extract_pullquotes(self):
        input_html = """<p>Some text[pullquote]with a pullquote[/pullquote]</p>"""
        output_pullquotes = extract_pullquotes(input_html)
        expected_pullquotes = ["with a pullquote"]
        self.assertEqual(output_pullquotes, expected_pullquotes)

    def test_extract_pullquotes_with_multiple_pullquotes(self):
        input_html = """<p>Some text[pullquote]with a pullquote[/pullquote] and another [pullquote]with a pullquote[/pullquote]</p>"""  # noqa: E501
        output_pullquotes = extract_pullquotes(input_html)
        expected_pullquotes = ["with a pullquote", "with a pullquote"]
        self.assertEqual(output_pullquotes, expected_pullquotes)

    def test_extract_pullquotes_with_none_as_input(self):
        input_html = None

        with self.assertRaises(TypeError):
            extract_pullquotes(input_html)
