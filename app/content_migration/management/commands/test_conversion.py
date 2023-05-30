# import SimpleTestCase
from django.test import SimpleTestCase

from .conversion import adapt_html_to_generic_blocks


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
