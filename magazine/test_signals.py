from django.test import TestCase

from contact.factories import PersonFactory
from contact.models import ContactPublicationStatistics
from magazine.factories import (
    MagazineArticleFactory,
    MagazineDepartmentFactory,
    MagazineIssueFactory,
)
from magazine.models import (
    ArchiveArticle,
    ArchiveArticleAuthor,
    ArchiveIssue,
    MagazineArticleAuthor,
)


class MagazineSignalsTest(TestCase):
    """Test the signals that update ContactPublicationStatistics when article author relationships change."""

    def setUp(self):
        """Set up test data."""
        # Create a person to be an author
        self.person = PersonFactory.create()

        # Create a department first (MagazineArticleFactory needs this)
        self.department = MagazineDepartmentFactory.create()

        # Create a magazine issue
        self.magazine_issue = MagazineIssueFactory.create()

        # Create a magazine article directly using factory (it will be attached to the magazine issue)
        self.magazine_article = MagazineArticleFactory.create(
            department=self.department,
        )

        # Get magazine index for creating archive issue
        magazine_index = self.magazine_issue.get_parent()

        # Create an archive issue
        self.archive_issue = ArchiveIssue(
            title="Archive Issue",
            slug="archive-issue",
            publication_date="2020-01-01",
            internet_archive_identifier="test-archive",
        )
        magazine_index.add_child(instance=self.archive_issue)

        # Create an archive article - properly using ArchiveArticle model, not Page
        self.archive_article = ArchiveArticle(
            title="Archive Article",
            toc_page_number=1,
            pdf_page_number=1,
            issue=self.archive_issue,
        )
        self.archive_article.save()

    def test_magazine_article_author_create(self):
        """Test that ContactPublicationStatistics is updated when a MagazineArticleAuthor is created."""
        # Verify no statistics exist yet
        self.assertEqual(ContactPublicationStatistics.objects.count(), 0)

        # Create a magazine article author relationship
        _ = MagazineArticleAuthor.objects.create(
            article=self.magazine_article,
            author=self.person,
        )

        # Check that statistics were created
        self.assertEqual(ContactPublicationStatistics.objects.count(), 1)

        # Get the statistics
        stats = ContactPublicationStatistics.objects.get(contact=self.person)

        # Verify the article count is correct
        self.assertEqual(stats.article_count, 1)
        self.assertEqual(
            stats.contact_type,
            ContactPublicationStatistics.ContactType.PERSON,
        )

    def test_magazine_article_author_delete(self):
        """Test that ContactPublicationStatistics is updated when a MagazineArticleAuthor is deleted."""
        # Create a magazine article author relationship
        article_author = MagazineArticleAuthor.objects.create(
            article=self.magazine_article,
            author=self.person,
        )

        # Check that statistics exist
        self.assertEqual(ContactPublicationStatistics.objects.count(), 1)
        self.assertEqual(
            ContactPublicationStatistics.objects.get(contact=self.person).article_count,
            1,
        )

        # Delete the relationship
        article_author.delete()

        # Check that statistics were updated
        self.assertEqual(ContactPublicationStatistics.objects.count(), 1)
        self.assertEqual(
            ContactPublicationStatistics.objects.get(contact=self.person).article_count,
            0,
        )

    def test_archive_article_author_create(self):
        """Test that ContactPublicationStatistics is updated when an ArchiveArticleAuthor is created."""
        # Verify no statistics exist yet
        self.assertEqual(ContactPublicationStatistics.objects.count(), 0)

        # Create an archive article author relationship
        _ = ArchiveArticleAuthor.objects.create(
            article=self.archive_article,
            author=self.person,
        )

        # Check that statistics were created
        self.assertEqual(ContactPublicationStatistics.objects.count(), 1)

        # Get the statistics
        stats = ContactPublicationStatistics.objects.get(contact=self.person)

        # Verify the article count is correct
        self.assertEqual(stats.article_count, 1)
        self.assertEqual(
            stats.contact_type,
            ContactPublicationStatistics.ContactType.PERSON,
        )

    def test_archive_article_author_delete(self):
        """Test that ContactPublicationStatistics is updated when an ArchiveArticleAuthor is deleted."""
        # Create an archive article author relationship
        archive_author = ArchiveArticleAuthor.objects.create(
            article=self.archive_article,
            author=self.person,
        )

        # Check that statistics exist
        self.assertEqual(ContactPublicationStatistics.objects.count(), 1)
        self.assertEqual(
            ContactPublicationStatistics.objects.get(contact=self.person).article_count,
            1,
        )

        # Delete the relationship
        archive_author.delete()

        # Check that statistics were updated
        self.assertEqual(ContactPublicationStatistics.objects.count(), 1)
        self.assertEqual(
            ContactPublicationStatistics.objects.get(contact=self.person).article_count,
            0,
        )

    def test_multiple_articles_count(self):
        """Test that ContactPublicationStatistics correctly counts multiple articles."""
        # Create two magazine article author relationships and one archive
        MagazineArticleAuthor.objects.create(
            article=self.magazine_article,
            author=self.person,
        )

        # Create another magazine article with the same department
        second_article = MagazineArticleFactory.create(
            department=self.department,
        )

        MagazineArticleAuthor.objects.create(
            article=second_article,
            author=self.person,
        )

        ArchiveArticleAuthor.objects.create(
            article=self.archive_article,
            author=self.person,
        )

        # Check that statistics were created and count is correct
        self.assertEqual(ContactPublicationStatistics.objects.count(), 1)
        self.assertEqual(
            ContactPublicationStatistics.objects.get(contact=self.person).article_count,
            3,
        )

        # Delete one relationship
        MagazineArticleAuthor.objects.filter(
            article=self.magazine_article,
            author=self.person,
        ).delete()

        # Check that statistics were updated
        self.assertEqual(
            ContactPublicationStatistics.objects.get(contact=self.person).article_count,
            2,
        )
