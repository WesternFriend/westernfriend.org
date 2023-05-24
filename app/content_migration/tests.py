from django.test import TestCase, SimpleTestCase
from wagtail.rich_text import RichText
from blocks.blocks import PullQuoteBlock

from bs4 import BeautifulSoup

from content_migration.management.commands.shared import (
    extract_image_urls,
    parse_body_blocks,
    remove_pullquote_tags,
    create_media_embed_block,
    extract_pullquotes,
)


class RemovePullquoteTagsSimpleTestCase(SimpleTestCase):
    def test_remove_pullquote_tags(self) -> None:
        soup_context = BeautifulSoup(
            """<p>Some text[pullquote]with a pullquote[/pullquote]</p>""",
            "html.parser",
        )  # noqa: E501
        input_bs4_tag = soup_context.find("p")
        output_bs4_tag = remove_pullquote_tags(input_bs4_tag)
        expected_bs4_tag = BeautifulSoup(
            """<p>Some textwith a pullquote</p>""",
            "html.parser",
        ).find("p")

        self.assertEqual(output_bs4_tag, expected_bs4_tag)

    def test_remove_pullquote_tags_with_multiple_pullquotes(self) -> None:
        soup_context = BeautifulSoup(
            """<p>Some text [pullquote]with a pullquote[/pullquote] and another [pullquote]with a pullquote[/pullquote]</p>""",  # noqa: E501
            "html.parser",
        )
        input_bs4_tag = soup_context.find("p")
        output_bs4_tag = remove_pullquote_tags(input_bs4_tag)  # type: ignore
        expected_bs4_tag = BeautifulSoup(
            """<p>Some text with a pullquote and another with a pullquote</p>""",
            "html.parser",
        ).find("p")

        self.assertEqual(output_bs4_tag, expected_bs4_tag)


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


class CreateMediaEmbedBlockTestCase(TestCase):
    def test_create_media_embed_block(self) -> None:
        self.MaxDiff = None
        input_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        output_media_embed_block = create_media_embed_block(input_url)

        self.assertEqual(
            output_media_embed_block[1].url,
            input_url,
        )


class TestExtractImages(SimpleTestCase):
    def test_extract_image_urls(self) -> None:
        input_html = (
            """<p>Some text<img src="https://www.example.com/image.jpg" /></p>"""
        )
        output_images = extract_image_urls(input_html)
        expected_images = ["https://www.example.com/image.jpg"]
        self.assertEqual(output_images, expected_images)


class ParseBodyBlocksTestCase(TestCase):
    def test_parse_body_blocks(self) -> None:
        self.MaxDiff = None
        input_html = """<p>Some text[pullquote]with a pullquote[/pullquote]</p>"""
        output_blocks = parse_body_blocks(input_html)
        expected_blocks = [
            (
                "pullquote",
                PullQuoteBlock("with a pullquote"),
            ),
            (
                "rich_text",
                RichText("Some text with a pullquote"),
            ),
        ]
        self.assertEqual(
            output_blocks[0][0],
            expected_blocks[0][0],
        )
        # TODO: Figure out how to compare
        # rendered output for PullQuoteBlock
        # self.assertEqual(
        #     type(output_blocks[0][1]),
        #     type(expected_blocks[0][1]),
        # )
