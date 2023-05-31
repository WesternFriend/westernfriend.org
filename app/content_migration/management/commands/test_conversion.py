# import SimpleTestCase
from django.test import SimpleTestCase

from .conversion import (
    adapt_html_to_generic_blocks,
    remove_pullquote_tags,
    extract_pullquotes,
)


class AdaptHtmlToGenericBlocksTest(SimpleTestCase):
    def test_adapt_html_to_generic_blocks(self) -> None:
        html_string = """<p>Some text</p><p>Some more text</p>"""

        generic_blocks = adapt_html_to_generic_blocks(html_string)

        self.assertEqual(len(generic_blocks), 1)
        self.assertEqual(generic_blocks[0].block_type, "rich_text")
        self.assertEqual(generic_blocks[0].block_content, html_string)

    def test_adapt_html_to_generic_blocks_with_image(self) -> None:
        html_string = """<p>Some text</p><p>Some more text</p><img src="https://example.com/image.jpg">"""

        generic_blocks = adapt_html_to_generic_blocks(html_string)

        self.assertEqual(len(generic_blocks), 2)
        self.assertEqual(generic_blocks[0].block_type, "rich_text")
        self.assertEqual(
            generic_blocks[0].block_content, """<p>Some text</p><p>Some more text</p>"""
        )
        self.assertEqual(generic_blocks[1].block_type, "image")
        self.assertEqual(
            generic_blocks[1].block_content,
            """<img src="https://example.com/image.jpg"/>""",
        )


class RemovePullquoteTagsSimpleTestCase(SimpleTestCase):
    def test_remove_pullquote_tags(self) -> None:
        input_html = """<p>Some text[pullquote]with a pullquote[/pullquote]</p>"""
        output_html = remove_pullquote_tags(input_html)

        expected_html = """<p>Some textwith a pullquote</p>"""

        self.assertEqual(output_html, expected_html)

    def test_remove_pullquote_tags_with_multiple_pullquotes(self) -> None:
        input_html = """<p>Some text [pullquote]with a pullquote[/pullquote] and another [pullquote]with a pullquote[/pullquote]</p>"""  # noqa: E501
        output_html = remove_pullquote_tags(input_html)
        expected_html = """<p>Some text with a pullquote and another with a pullquote</p>"""  # noqa: E501

        self.assertEqual(output_html, expected_html)


class ExtractPullquotesSimpleTestCase(SimpleTestCase):
    def test_extract_pullquotes(self) -> None:
        input_html = """<p>Some text[pullquote]with a pullquote[/pullquote]</p>"""
        output_pullquotes = extract_pullquotes(input_html)
        expected_pullquotes = ["with a pullquote"]
        self.assertEqual(output_pullquotes, expected_pullquotes)

    def test_extract_pullquotes_with_multiple_pullquotes(self) -> None:
        input_html = """<p>Some text[pullquote]with a pullquote[/pullquote] and another [pullquote]with a pullquote[/pullquote]</p>"""  # noqa: E501
        output_pullquotes = extract_pullquotes(input_html)
        expected_pullquotes = ["with a pullquote", "with a pullquote"]
        self.assertEqual(output_pullquotes, expected_pullquotes)

    def test_extract_pullquotes_with_none_as_input(self) -> None:
        input_html = None

        with self.assertRaises(TypeError):
            extract_pullquotes(input_html)  # type: ignore
