import datetime as dt

from django.core.cache import cache
from django.db import connection
from django.test import RequestFactory, TestCase
from django.test.utils import CaptureQueriesContext
from django.utils import timezone
from wagtail.images import get_image_model
from wagtail.images.tests.utils import get_test_image_file
from wagtail.models import Page, Site

from common.fake_content import image_block
from contact.models import Meeting, MeetingIndexPage
from documents.factories import MeetingDocumentFactory, PublicBoardDocumentFactory
from documents.models import (
    BODY_IMAGE_RENDITION_SPEC,
    MeetingDocument,
    MeetingDocumentIndexPage,
    PublicBoardDocument,
    PublicBoardDocumentIndexPage,
)
from home.models import HomePage


class TestMeetingDocumentIndexPage(TestCase):
    def setUp(self) -> None:
        self.factory = RequestFactory()

        # Set up the page hierarchy
        site_root = Page.objects.get(id=2)
        self.home_page = HomePage(title="Home")
        site_root.add_child(instance=self.home_page)
        Site.objects.all().update(root_page=self.home_page)

        # Create meeting index and meeting
        self.meeting_index = MeetingIndexPage(title="Meetings")
        self.home_page.add_child(instance=self.meeting_index)

        self.meeting = Meeting(title="Test Meeting")
        self.meeting_index.add_child(instance=self.meeting)

        # Create document index
        self.document_index = MeetingDocumentIndexPage(title="Meeting Documents")
        self.home_page.add_child(instance=self.document_index)

    def test_get_context(self) -> None:
        """Test that get_context returns documents with publishing_meeting prefetched."""
        # Create some meeting documents
        document1 = MeetingDocument(
            title="Document 1",
            publishing_meeting=self.meeting,
            publication_date=timezone.localdate(),
            document_type="minute",
        )
        document2 = MeetingDocument(
            title="Document 2",
            publishing_meeting=self.meeting,
            publication_date=timezone.localdate() - dt.timedelta(days=1),
            document_type="epistle",
        )

        self.document_index.add_child(instance=document1)
        self.document_index.add_child(instance=document2)

        request = self.factory.get("/")
        context = self.document_index.get_context(request)

        self.assertIn("meeting_documents", context)
        # The context should have the documents with publishing_meeting prefetched
        meeting_documents = list(context["meeting_documents"])
        self.assertEqual(len(meeting_documents), 2)
        self.assertIn(document1, meeting_documents)
        self.assertIn(document2, meeting_documents)

        with self.assertNumQueries(0):
            publishing_meeting_pks = [
                document.publishing_meeting.pk for document in meeting_documents
            ]

        self.assertEqual(
            publishing_meeting_pks,
            [self.meeting.pk, self.meeting.pk],
        )


class DocumentFactoryTest(TestCase):
    def test_meeting_document_factory_creates_its_index_page(self) -> None:
        document = MeetingDocumentFactory.create()

        self.assertIsInstance(document.get_parent().specific, MeetingDocumentIndexPage)
        self.assertIn(document.publishing_meeting.title, document.title)
        self.assertTrue(document.body)

        # A second document reuses the existing index page.
        second = MeetingDocumentFactory.create()
        self.assertEqual(second.get_parent(), document.get_parent())

    def test_public_board_document_factory_creates_its_index_page(self) -> None:
        document = PublicBoardDocumentFactory.create()

        self.assertIsInstance(
            document.get_parent().specific,
            PublicBoardDocumentIndexPage,
        )
        self.assertTrue(document.body)


def _queries_matching(captured, fragment: str) -> int:
    return sum(fragment in query["sql"] for query in captured)


class TestPublicBoardDocumentQueryCounts(TestCase):
    def setUp(self) -> None:
        site_root = Page.objects.get(id=2)
        self.home_page = HomePage(title="Home", slug="home")
        site_root.add_child(instance=self.home_page)
        Site.objects.all().update(root_page=self.home_page, hostname="testserver")
        Site.clear_site_root_paths_cache()
        self.addCleanup(Site.clear_site_root_paths_cache)

        self.index = PublicBoardDocumentIndexPage(
            title="Board Documents",
            slug="board",
        )
        self.home_page.add_child(instance=self.index)
        self.image_model = get_image_model()

    def _image(self, title: str):
        return self.image_model.objects.create(
            title=title,
            file=get_test_image_file(filename=f"{title}.gif"),
        )

    def _document(
        self,
        title: str,
        *,
        images=None,
        category: str = PublicBoardDocument.PublicBoardDocmentCategoryChoices.BOARD_PHOTOS,
        live: bool = True,
        prepare_renditions: bool = True,
    ) -> PublicBoardDocument:
        images = images or []
        if prepare_renditions:
            for image in images:
                image.get_rendition(BODY_IMAGE_RENDITION_SPEC)
        document = PublicBoardDocument(
            title=title,
            slug=title.lower().replace(" ", "-"),
            publication_date=timezone.localdate(),
            category=category,
            body=[image_block(image) for image in images]
            or [("rich_text", "<p>Note</p>")],
        )
        self.index.add_child(instance=document)
        if not live:
            document.unpublish()
        return document

    def _get(self, url: str):
        cache.clear()
        Site.clear_site_root_paths_cache()
        with CaptureQueriesContext(connection) as captured:
            response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        return response, captured

    def test_rendition_queries_do_not_grow_with_images(self) -> None:
        one = self._document("One photo", images=[self._image("one")])
        _, one_queries = self._get(one.url)
        several_images = [self._image(f"photo-{index}") for index in range(4)]
        several = self._document("Several photos", images=several_images)
        several_response, several_queries = self._get(several.url)

        one_renditions = _queries_matching(one_queries, "wagtailimages_rendition")
        several_renditions = _queries_matching(
            several_queries,
            "wagtailimages_rendition",
        )
        self.assertEqual(several_renditions, one_renditions)
        self.assertLessEqual(several_renditions, 1)
        for image in several_images:
            rendition = image.get_rendition(BODY_IMAGE_RENDITION_SPEC)
            self.assertContains(several_response, rendition.url)

    def test_cold_renditions_do_not_query_per_image(self) -> None:
        one_image = self._image("cold-one")
        one = self._document(
            "Cold one",
            images=[one_image],
            prepare_renditions=False,
        )
        one_response, one_queries = self._get(one.url)
        several_images = [self._image(f"cold-{index}") for index in range(4)]
        several = self._document(
            "Cold several",
            images=several_images,
            prepare_renditions=False,
        )
        several_response, several_queries = self._get(several.url)

        one_renditions = _queries_matching(one_queries, "wagtailimages_rendition")
        several_renditions = _queries_matching(
            several_queries,
            "wagtailimages_rendition",
        )
        self.assertEqual(several_renditions, one_renditions)
        self.assertLessEqual(several_renditions, 3)
        for image in [one_image, *several_images]:
            rendition = image.get_rendition(BODY_IMAGE_RENDITION_SPEC)
            self.assertContains(
                several_response if image in several_images else one_response,
                rendition.url,
            )

    def test_index_queries_do_not_grow_with_documents(self) -> None:
        self._document("Alpha")
        self.client.get(self.index.url)
        _, one_queries = self._get(self.index.url)
        for index in range(4):
            self._document(f"More {index}")
        _, several_queries = self._get(self.index.url)

        self.assertEqual(len(several_queries), len(one_queries))

    def test_index_lists_live_documents_grouped_by_category(self) -> None:
        photos = self._document("Board day")
        reports = self._document(
            "Annual report",
            category=PublicBoardDocument.PublicBoardDocmentCategoryChoices.ANNUAL_REPORTS,
        )
        draft = self._document("Hidden draft", live=False)

        response, _captured = self._get(self.index.url)
        content = response.content.decode()

        self.assertIn(photos.title, content)
        self.assertIn(reports.title, content)
        self.assertNotIn(draft.title, content)
        self.assertLess(
            content.index("Annual Reports"),
            content.index("Board Photos"),
        )
