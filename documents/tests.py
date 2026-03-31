import datetime

from django.test import RequestFactory, TestCase
from wagtail.models import Page, Site

from contact.models import Meeting, MeetingIndexPage
from documents.models import MeetingDocument, MeetingDocumentIndexPage
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
            publication_date=datetime.date.today(),
            document_type="minute",
        )
        document2 = MeetingDocument(
            title="Document 2",
            publishing_meeting=self.meeting,
            publication_date=datetime.date.today() - datetime.timedelta(days=1),
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
