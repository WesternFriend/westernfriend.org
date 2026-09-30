from unittest.mock import Mock

from django.test import TestCase

from .blocks import HeadingBlock, MediaBlock, PullQuoteBlock


class MediaBlockTest(TestCase):
    def setUp(self) -> None:
        self.block = MediaBlock()

    def test_render_basic_no_value(self) -> None:
        result = self.block.render_basic(None)
        self.assertEqual(result, "")

    def test_render_basic_video(self) -> None:
        # Create a mock media object with type == "video"
        mock_media = Mock()
        mock_media.type = "video"
        mock_media.width = 400
        mock_media.height = 300
        mock_media.sources = [{"src": "test_source.mp4", "type": "video/mp4"}]

        result = self.block.render_basic(mock_media)

        # Check that the result matches expectations
        self.assertIn('<video width="400" height="300" controls>', result)

    def test_render_basic_audio(self) -> None:
        # Create a mock media object with type == "audio"
        mock_media = Mock()
        mock_media.type = "audio"
        mock_media.sources = [{"src": "test_source.mp3", "type": "audio/mpeg"}]

        result = self.block.render_basic(mock_media)

        # Check that the result matches expectations
        self.assertIn("<audio controls>", result)


class TestPullQuoteBlock(TestCase):
    def setUp(self) -> None:
        self.block = PullQuoteBlock()

    def test_render_basic_with_value(self) -> None:
        # Render the block with a value
        html = self.block.render_basic("This is a pull quote")

        # Assert that the value is correctly wrapped in a div with the class 'pullquote'
        self.assertEqual(html, '<div class="pullquote">This is a pull quote</div>')

    def test_render_basic_without_value(self) -> None:
        # Render the block with no value
        html = self.block.render_basic(None)  # type: ignore

        # Assert that an empty string is returned
        self.assertEqual(html, "")

        # Also test with an empty string as input
        html = self.block.render_basic("")

        # Assert that an empty string is returned
        self.assertEqual(html, "")


class HeadingBlockTest(TestCase):
    def setUp(self) -> None:
        self.block = HeadingBlock()

    def test_render_ignores_legacy_color_and_emits_no_inline_style(self) -> None:
        # A heading saved before the color field was removed still carries a
        # stored "color" key in its StreamField data. It must be ignored, and
        # the rendered heading must not emit any inline color styling
        # (WCAG 1.4.3 - see #1299).
        value = self.block.to_python(
            {
                "heading_level": "h2",
                "heading_text": "Accessible Heading",
                "target_slug": "accessible-heading",
                "color": "#ff0000",  # legacy value, no longer a field
            },
        )

        html = self.block.render(value)

        self.assertIn("Accessible Heading", html)
        self.assertIn('id="accessible-heading"', html)
        self.assertIn("<h2", html)
        self.assertIn("</h2>", html)
        self.assertNotIn("style=", html)
        self.assertNotIn("#ff0000", html)
