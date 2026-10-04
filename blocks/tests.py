from unittest.mock import Mock

from django.core.exceptions import ValidationError
from django.test import TestCase

from .blocks import (
    MediaBlock,
    MediaChooserBlock,
    PullQuoteBlock,
    validate_webvtt_document,
)


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


class ValidateWebVttDocumentTest(TestCase):
    @staticmethod
    def _document(extension: str) -> Mock:
        document = Mock()
        document.file_extension = extension
        document.filename = f"captions.{extension}"
        return document

    def test_accepts_a_vtt_document(self) -> None:
        validate_webvtt_document(self._document("vtt"))

    def test_accepts_an_uppercase_extension(self) -> None:
        # Document.file_extension is not lower-cased, so a .VTT upload is valid.
        validate_webvtt_document(self._document("VTT"))

    def test_rejects_a_document_that_is_not_vtt(self) -> None:
        with self.assertRaises(ValidationError):
            validate_webvtt_document(self._document("pdf"))

    def test_rejects_a_document_with_no_extension(self) -> None:
        with self.assertRaises(ValidationError):
            validate_webvtt_document(self._document(""))


class MediaChooserBlockTest(TestCase):
    def setUp(self) -> None:
        self.block = MediaChooserBlock()

    def test_render_basic_names_the_media(self) -> None:
        # The comparison view renders this, so an empty string would leave the
        # Media row blank when the media is swapped.
        media = Mock()
        media.title = "An interview"
        self.assertEqual(self.block.render_basic(media), "An interview")

    def test_render_basic_escapes_the_title(self) -> None:
        media = Mock()
        media.title = "<script>alert(1)</script>"
        self.assertNotIn("<script>", self.block.render_basic(media))

    def test_render_basic_without_value(self) -> None:
        self.assertEqual(self.block.render_basic(None), "")


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
