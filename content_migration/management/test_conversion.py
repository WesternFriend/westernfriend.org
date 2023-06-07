from unittest.mock import patch
from django.test import SimpleTestCase, TestCase
import requests
from content_migration.management.conversion import (
    adapt_html_to_generic_blocks,
    BlockFactory,
    create_image_block,
    extract_image_urls,
    GenericBlock,
    remove_pullquote_tags,
    extract_pullquotes,
)
from content_migration.management.constants import (
    WESTERN_FRIEND_LOGO_URL,
    WESTERN_FRIEND_LOGO_FILE_NAME,
)
from content_migration.management.errors import BlockFactoryError


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


class AdaptHtmlToGenericBlockTest(SimpleTestCase):
    def test_adapt_html_to_generic_blocks(self) -> None:
        html_string = """<p>Some text</p><p>Some more text</p>"""

        generic_blocks = adapt_html_to_generic_blocks(html_string)

        self.assertEqual(len(generic_blocks), 1)
        self.assertEqual(generic_blocks[0].block_type, "rich_text")
        self.assertEqual(generic_blocks[0].block_content, html_string)

    def test_adapt_html_to_generic_blocks_with_pullquote(self) -> None:
        html_string = """<p>Some text</p><p>Some more text</p><p>A paragraph with [pullquote]a pullquote[/pullquote] that should be extracted</p>"""  # noqa: E501

        generic_blocks = adapt_html_to_generic_blocks(html_string)

        self.assertEqual(len(generic_blocks), 3)
        self.assertEqual(generic_blocks[0].block_type, "rich_text")
        self.assertEqual(
            generic_blocks[0].block_content, """<p>Some text</p><p>Some more text</p>"""
        )
        self.assertEqual(generic_blocks[1].block_type, "pullquote")
        self.assertEqual(generic_blocks[1].block_content, "a pullquote")
        self.assertEqual(generic_blocks[2].block_type, "rich_text")
        self.assertEqual(
            generic_blocks[2].block_content,
            "<p>A paragraph with a pullquote that should be extracted</p>",
        )

    def test_adapt_html_to_generic_blocks_with_image(self) -> None:
        html_string = (
            """<p>Some text</p><p><img src="https://www.example.com/image.jpg" /></p>"""
        )

        generic_blocks = adapt_html_to_generic_blocks(html_string)

        self.assertEqual(len(generic_blocks), 2)
        self.assertEqual(generic_blocks[0].block_type, "rich_text")
        self.assertEqual(generic_blocks[0].block_content, """<p>Some text</p>""")
        self.assertEqual(generic_blocks[1].block_type, "image")
        self.assertEqual(
            generic_blocks[1].block_content,
            "https://www.example.com/image.jpg",
        )


class CreateImageBlockTestCase(TestCase):
    def test_create_image_block(self) -> None:
        # use existing WesternFriend logo URL
        input_html = (
            f"""<p><img src="{ WESTERN_FRIEND_LOGO_URL }" /></p>"""  # noqa: E501
        )

        image_urls = extract_image_urls(input_html)

        image_block = create_image_block(image_urls[0])

        # self.assertEqual(image_block.block_type, "image")  # type: ignore
        self.assertEqual(
            image_block["image"].title,
            WESTERN_FRIEND_LOGO_FILE_NAME,
        )  # type: ignore

    def test_create_image_block_with_none_as_input(self) -> None:
        input_html = None

        with self.assertRaises(requests.exceptions.MissingSchema):
            create_image_block(input_html)  # type: ignore

    def test_create_image_block_with_invalid_url(self) -> None:
        input_html = "/image.jpg"

        with self.assertRaises(requests.exceptions.MissingSchema):
            create_image_block(input_html)


class BlockFactorySimpleTestCase(SimpleTestCase):
    # it should raise a ValueError if the block type is not supported
    def test_block_factory_with_invalid_block_type(self) -> None:
        generic_block = GenericBlock(
            "invalid_block_type",
            "some content",
        )

        with self.assertRaises(ValueError):
            BlockFactory.create_block(
                generic_block=generic_block,
            )

    def test_create_block_invalid_image_url_missing_schema(self) -> None:
        invalid_url_block = GenericBlock("image", "invalid_url")
        with patch(
            "content_migration.management.conversion.create_image_block"
        ) as mock_create_image_block:
            mock_create_image_block.side_effect = requests.exceptions.MissingSchema
            with self.assertRaises(BlockFactoryError) as cm:
                BlockFactory.create_block(invalid_url_block)
            self.assertEqual(str(cm.exception), "Invalid image URL: missing schema")

    def test_create_block_invalid_image_url_invalid_schema(self) -> None:
        invalid_url_block = GenericBlock("image", "invalid_url")
        with patch(
            "content_migration.management.conversion.create_image_block"
        ) as mock_create_image_block:
            mock_create_image_block.side_effect = requests.exceptions.InvalidSchema
            with self.assertRaises(BlockFactoryError) as cm:
                BlockFactory.create_block(invalid_url_block)
            self.assertEqual(str(cm.exception), "Invalid image URL: invalid schema")
