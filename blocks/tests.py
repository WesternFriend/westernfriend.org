import shutil
import tempfile
from contextlib import nullcontext
from html.parser import HTMLParser
from io import BytesIO
from unittest.mock import Mock

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from wagtail.blocks import StreamValue
from wagtail.documents.models import Document
from wagtail.models import Collection, CollectionViewRestriction, Page, Site
from wagtailmedia.models import get_media_model

from library.models import LibraryItem

from .blocks import (
    ButtonBlock,
    HeadingBlock,
    MediaBlock,
    MediaChooserBlock,
    PageCardBlock,
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


def _mock_captions() -> Mock:
    captions = Mock()
    captions.id = 1
    captions.filename = "captions.vtt"
    # Wagtail's own document URL, which the track must not use.
    captions.url = "/documents/1/captions.vtt"
    return captions


class _TrackParentParser(HTMLParser):
    """Record each <track> with the element it sits directly inside."""

    VOID_ELEMENTS = {"source", "track", "br", "img", "input", "hr"}

    def __init__(self) -> None:
        super().__init__()
        self.open_elements: list[str] = []
        self.tracks: list[tuple[str, str]] = []

    def handle_starttag(self, tag, attrs) -> None:
        if tag == "track":
            parent = self.open_elements[-1] if self.open_elements else ""
            self.tracks.append((parent, dict(attrs).get("src", "")))
        if tag not in self.VOID_ELEMENTS:
            self.open_elements.append(tag)

    def handle_endtag(self, tag) -> None:
        if tag in self.open_elements:
            while self.open_elements.pop() != tag:
                pass


def _track_parents(html: str) -> list[tuple[str, str]]:
    parser = _TrackParentParser()
    parser.feed(html)
    return parser.tracks


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

    def test_renders_caption_track_inside_the_video(self) -> None:
        html = self.block.render(
            {
                "media": _mock_media("video"),
                "captions": _mock_captions(),
                "transcript": "",
            },
        )
        # A track outside the player is never tied to it, so check the parent.
        self.assertEqual(
            _track_parents(html),
            [("video", "/documents/captions/1/captions.vtt")],
        )

    def test_renders_caption_track_inside_the_audio(self) -> None:
        html = self.block.render(
            {
                "media": _mock_media("audio"),
                "captions": _mock_captions(),
                "transcript": "",
            },
        )
        self.assertEqual(
            _track_parents(html),
            [("audio", "/documents/captions/1/captions.vtt")],
        )

    def test_caption_track_is_served_from_this_origin(self) -> None:
        # Wagtail's own document URL redirects to remote storage, which a
        # same-origin <track> request cannot follow.
        html = self.block.render(
            {
                "media": _mock_media("video"),
                "captions": _mock_captions(),
                "transcript": "",
            },
        )
        [(_, src)] = _track_parents(html)
        self.assertEqual(src, reverse("serve_captions", args=[1, "captions.vtt"]))
        self.assertNotEqual(src, _mock_captions().url)

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

    def test_transcript_is_wrapped_in_prose(self) -> None:
        # Rich text output can only be styled through the prose class.
        html = self.block.render(
            {
                "media": _mock_media("video"),
                "captions": None,
                "transcript": "<p>A spoken transcript.</p>",
            },
        )
        self.assertRegex(
            html,
            r'<div class="prose">\s*<p>A spoken transcript\.</p>',
        )

    def test_no_transcript_section_without_transcript(self) -> None:
        html = self.block.render(
            {"media": _mock_media("video"), "captions": None, "transcript": ""},
        )
        self.assertNotIn('class="transcript"', html)


class ValidateWebVttDocumentTest(TestCase):
    @staticmethod
    def _document(extension: str, contents: bytes = b"WEBVTT\n") -> Mock:
        document = Mock()
        document.file_extension = extension
        document.filename = f"captions.{extension}"
        document.open_file = lambda: nullcontext(BytesIO(contents))
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

    def test_accepts_a_byte_order_mark_before_the_signature(self) -> None:
        # Editors that save UTF-8 with a BOM are still writing valid WebVTT.
        validate_webvtt_document(
            self._document("vtt", b"\xef\xbb\xbfWEBVTT\n\n00:00.000 --> 00:01.000\n"),
        )

    def test_accepts_what_the_spec_allows_after_the_signature(self) -> None:
        for contents in (
            b"WEBVTT Kind: captions\n",
            b"WEBVTT\tTitle\n",
            b"WEBVTT\r\n",
            b"WEBVTT",
        ):
            with self.subTest(contents=contents):
                validate_webvtt_document(self._document("vtt", contents))

    def test_rejects_a_vtt_document_without_the_signature(self) -> None:
        # The extension alone lets a renamed SubRip file through, and the
        # browser can't parse it as captions.
        for contents in (
            b"1\n00:00:00,000 --> 00:00:01,000\nHello\n",
            b"%PDF-1.4",
            b"",
            b"WEBVTTX\n",
            b"webvtt\n",
            b" WEBVTT\n",
        ):
            with self.subTest(contents=contents):
                with self.assertRaises(ValidationError) as raised:
                    validate_webvtt_document(self._document("vtt", contents))
                self.assertIn("does not start with WEBVTT", str(raised.exception))


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


class _TemporaryMediaRootMixin:
    """Keep uploaded test files out of the real media folder."""

    @classmethod
    def setUpClass(cls) -> None:
        media_root = tempfile.mkdtemp(prefix="media-block-tests-")
        cls.addClassCleanup(shutil.rmtree, media_root, ignore_errors=True)
        cls.enterClassContext(override_settings(MEDIA_ROOT=media_root))
        super().setUpClass()


class MediaBlockCaptionsValidationTest(_TemporaryMediaRootMixin, TestCase):
    """The captions chooser must reject a non-WebVTT document *through the block*,
    not only via the standalone validator. Otherwise the validator could exist
    but never run when an editor selects a file, and the direct-call test above
    would still pass.
    """

    @staticmethod
    def _captions_block():
        return MediaBlock().child_blocks["captions"]

    def test_block_rejects_a_non_vtt_caption_document(self) -> None:
        pdf = Document.objects.create(
            title="not captions",
            file=SimpleUploadedFile("notes.pdf", b"%PDF-1.4"),
        )
        with self.assertRaises(ValidationError):
            self._captions_block().clean(pdf)

    def test_block_accepts_a_vtt_caption_document(self) -> None:
        vtt = Document.objects.create(
            title="captions",
            file=SimpleUploadedFile("captions.vtt", b"WEBVTT\n"),
        )
        self.assertEqual(self._captions_block().clean(vtt), vtt)

    def test_block_rejects_a_vtt_document_that_is_not_webvtt(self) -> None:
        srt = Document.objects.create(
            title="renamed subrip",
            file=SimpleUploadedFile(
                "renamed.vtt",
                b"1\n00:00:00,000 --> 00:00:01,000\nHello\n",
            ),
        )
        with self.assertRaises(ValidationError):
            self._captions_block().clean(srt)

    def test_block_accepts_a_webvtt_document_with_a_byte_order_mark(self) -> None:
        vtt = Document.objects.create(
            title="captions with a BOM",
            file=SimpleUploadedFile("bom.vtt", b"\xef\xbb\xbfWEBVTT\n"),
        )
        self.assertEqual(self._captions_block().clean(vtt), vtt)

    def test_optional_empty_caption_is_valid(self) -> None:
        # required=False, so no selection must stay valid.
        self.assertIsNone(self._captions_block().clean(None))


class MediaBlockLegacyValueTest(_TemporaryMediaRootMixin, TestCase):
    """Library bodies saved before captions existed store a bare media id."""

    @classmethod
    def setUpTestData(cls) -> None:
        cls.media = get_media_model().objects.create(
            title="An interview",
            file=ContentFile(b"not really a video", name="interview.mp4"),
            type="video",
        )

    def test_to_python_reads_a_bare_media_id(self) -> None:
        value = MediaBlock().to_python(self.media.id)
        self.assertEqual(value["media"], self.media)
        self.assertIsNone(value["captions"])
        self.assertEqual(value["transcript"].source, "")

    def test_bulk_to_python_reads_bare_ids_and_new_values(self) -> None:
        legacy, current = MediaBlock().bulk_to_python(
            [self.media.id, {"media": self.media.id, "transcript": "<p>Hi</p>"}],
        )
        self.assertEqual(legacy["media"], self.media)
        self.assertEqual(current["media"], self.media)
        self.assertEqual(current["transcript"].source, "<p>Hi</p>")

    def test_saved_library_body_with_a_bare_id_still_renders(self) -> None:
        stream_block = LibraryItem._meta.get_field("body").stream_block
        body = StreamValue(
            stream_block,
            [{"type": "media", "value": self.media.id, "id": "legacy"}],
            is_lazy=True,
        )
        html = body.render_as_block()
        self.assertIn("<video", html)
        self.assertIn(self.media.url, html)


class ServeCaptionsViewTest(_TemporaryMediaRootMixin, TestCase):
    CAPTIONS = b"WEBVTT\n\n00:00.000 --> 00:01.000\nHello\n"

    @classmethod
    def setUpTestData(cls) -> None:
        cls.captions = Document.objects.create(
            title="captions",
            file=ContentFile(cls.CAPTIONS, name="captions.vtt"),
        )

    @staticmethod
    def _url(document, filename=None) -> str:
        return reverse(
            "serve_captions",
            args=[document.id, filename or document.filename],
        )

    def test_serves_the_captions_as_webvtt(self) -> None:
        response = self.client.get(self._url(self.captions))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/vtt; charset=utf-8")
        self.assertEqual(response["X-Content-Type-Options"], "nosniff")
        self.assertEqual(b"".join(response.streaming_content), self.CAPTIONS)

    @override_settings(WAGTAILDOCS_SERVE_METHOD="redirect")
    def test_streams_where_the_document_url_would_redirect(self) -> None:
        # Production storage makes Wagtail's document view redirect.
        self.assertEqual(self.client.get(self.captions.url).status_code, 302)
        response = self.client.get(self._url(self.captions))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(b"".join(response.streaming_content), self.CAPTIONS)

    def test_wrong_filename_is_not_found(self) -> None:
        response = self.client.get(self._url(self.captions, "other.vtt"))
        self.assertEqual(response.status_code, 404)

    def test_a_document_that_is_not_vtt_is_not_found(self) -> None:
        pdf = Document.objects.create(
            title="notes",
            file=ContentFile(b"%PDF-1.4", name="notes.pdf"),
        )
        self.assertEqual(self.client.get(self._url(pdf)).status_code, 404)

    def test_a_vtt_document_without_the_signature_is_not_found(self) -> None:
        renamed = Document.objects.create(
            title="notes",
            file=ContentFile(b"%PDF-1.4", name="notes.vtt"),
        )
        self.assertEqual(self.client.get(self._url(renamed)).status_code, 404)

    def test_post_is_not_allowed(self) -> None:
        self.assertEqual(self.client.post(self._url(self.captions)).status_code, 405)

    def test_private_collection_captions_need_a_login(self) -> None:
        private = Collection.get_first_root_node().add_child(name="Private")
        CollectionViewRestriction.objects.create(
            collection=private,
            restriction_type=CollectionViewRestriction.LOGIN,
        )
        self.captions.collection = private
        self.captions.save()

        response = self.client.get(self._url(self.captions))
        self.assertEqual(response.status_code, 302)
        self.assertNotIn(b"Hello", response.content)

        user = get_user_model().objects.create_user(
            email="reader@example.com",
            password="a-long-test-password",
        )
        self.client.force_login(user)
        response = self.client.get(self._url(self.captions))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(b"".join(response.streaming_content), self.CAPTIONS)


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


class PageCardBlockTest(TestCase):
    def test_page_card_links_to_its_page(self) -> None:
        root_page = Site.objects.get(is_default_site=True).root_page
        page = root_page.add_child(instance=Page(title="About", slug="about"))
        block = PageCardBlock()
        value = block.to_python({"page": page.id, "text": "Card text"})

        html = block.render(value)

        self.assertIn(f'href="{page.url}"', html)
        self.assertIn('aria-label="Go to About"', html)


class PageLinkBlocksWithoutPageTest(TestCase):
    """A chosen page that was later deleted resolves to None and must still render."""

    def test_page_card_without_page_renders_without_link(self) -> None:
        block = PageCardBlock()
        value = block.to_python({"page": None, "text": "Card text"})

        html = block.render(value)

        self.assertIn("Card text", html)
        self.assertNotIn("<a ", html)

    def test_button_without_page_renders_empty_href(self) -> None:
        block = ButtonBlock()
        value = block.to_python({"button_text": "Read more", "page_link": None})

        html = block.render(value)

        self.assertIn("Read more", html)
        self.assertIn('href=""', html)
