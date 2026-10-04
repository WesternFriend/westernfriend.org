from unittest.mock import Mock

from django.test import TestCase

from .blocks import MediaBlock, PullQuoteBlock


def _mock_media(media_type: str = "video") -> Mock:
    media = Mock()
    media.type = media_type
    media.width = 400
    media.height = 300
    media.sources = [{"src": "test_source.mp4", "type": "video/mp4"}]
    return media


class MediaBlockTest(TestCase):
    def setUp(self) -> None:
        self.block = MediaBlock()

    def test_render_no_media(self) -> None:
        html = self.block.render(
            {"media": None, "captions": None, "transcript": ""},
        )
        self.assertEqual(html.strip(), "")

    def test_render_video(self) -> None:
        html = self.block.render(
            {"media": _mock_media("video"), "captions": None, "transcript": ""},
        )
        self.assertIn('<video width="400" height="300" controls>', html)
        self.assertIn('<source src="test_source.mp4" type="video/mp4">', html)

    def test_render_audio(self) -> None:
        media = _mock_media("audio")
        media.sources = [{"src": "test_source.mp3", "type": "audio/mpeg"}]
        html = self.block.render(
            {"media": media, "captions": None, "transcript": ""},
        )
        self.assertIn("<audio controls>", html)
        self.assertIn('<source src="test_source.mp3" type="audio/mpeg">', html)

    def test_renders_caption_track_when_captions_present(self) -> None:
        captions = Mock()
        captions.url = "/documents/1/captions.vtt"
        html = self.block.render(
            {
                "media": _mock_media("video"),
                "captions": captions,
                "transcript": "",
            },
        )
        self.assertIn(
            '<track kind="captions" src="/documents/1/captions.vtt"',
            html,
        )

    def test_no_caption_track_without_captions(self) -> None:
        html = self.block.render(
            {"media": _mock_media("video"), "captions": None, "transcript": ""},
        )
        self.assertNotIn("<track", html)

    def test_renders_transcript_when_present(self) -> None:
        html = self.block.render(
            {
                "media": _mock_media("video"),
                "captions": None,
                "transcript": "<p>A spoken transcript.</p>",
            },
        )
        self.assertIn('class="transcript"', html)
        self.assertIn("A spoken transcript.", html)

    def test_no_transcript_section_without_transcript(self) -> None:
        html = self.block.render(
            {"media": _mock_media("video"), "captions": None, "transcript": ""},
        )
        self.assertNotIn('class="transcript"', html)


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
