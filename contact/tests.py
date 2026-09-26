import datetime
import json
import re

from django.contrib.auth.models import AnonymousUser
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import RequestFactory, TestCase, TransactionTestCase
from wagtail.models import Locale, Page, Revision

from community.factories import OnlineWorshipFactory
from community.models import CommunityPage
from contact.factories import (
    MeetingFactory,
    MeetingIndexPageFactory,
    OrganizationFactory,
    OrganizationIndexPageFactory,
    PersonFactory,
    PersonIndexPageFactory,
)
from contact.models import (
    Meeting,
    MeetingAddress,
    MeetingIndexPage,
    MeetingPresidingClerk,
    MeetingWorshipTime,
    Organization,
    OrganizationIndexPage,
    Person,
    PersonIndexPage,
)
from library.factories import LibraryItemFactory
from library.models import LibraryItemAuthor
from magazine.factories import MagazineArticleFactory
from magazine.models import (
    ArchiveArticle,
    ArchiveArticleAuthor,
    ArchiveIssue,
    DeepArchiveIndexPage,
    MagazineArticleAuthor,
)
from memorials.factories import MemorialFactory
from store.factories import ProductFactory
from store.models import Book, BookAuthor


class PersonIndexPageFactoryTest(TestCase):
    def test_person_index_page_creation(self) -> None:
        # Create a PersonIndexPage instance
        person_index_page = PersonIndexPageFactory.create()

        # Now test that it was created
        self.assertIsNotNone(person_index_page)
        self.assertIsInstance(
            person_index_page,
            PersonIndexPage,
        )

        # Test that the PersonIndexPage instance has a parent
        self.assertIsInstance(
            person_index_page.get_parent().specific,
            CommunityPage,
        )


class PersonFactoryTest(TestCase):
    def test_person_index_page_creation(self) -> None:
        # Create a Person instance
        person = PersonFactory.create()

        # Now test that it was created
        self.assertIsNotNone(person)
        self.assertIsInstance(
            person,
            Person,
        )

        # Test that the Person instance has a PersonIndexPage parent
        self.assertIsInstance(
            person.get_parent().specific,
            PersonIndexPage,
        )


class MeetingIndexPageFactoryTest(TestCase):
    def test_meeting_index_page_creation(self) -> None:
        # Create a MeetingIndexPage instance
        meeting_index_page = MeetingIndexPageFactory.create()

        # Now test that it was created
        self.assertIsNotNone(meeting_index_page)
        self.assertIsInstance(
            meeting_index_page,
            MeetingIndexPage,
        )

        # Test that the MeetingIndexPage instance has a parent
        self.assertIsInstance(
            meeting_index_page.get_parent().specific,
            CommunityPage,
        )


class MeetingFactoryTest(TestCase):
    def test_meeting_index_page_creation(self) -> None:
        # Create a Meeting instance
        meeting = MeetingFactory.create()

        # Now test that it was created
        self.assertIsNotNone(meeting)
        self.assertIsInstance(
            meeting,
            Meeting,
        )

        # Test that the Meeting instance has a MeetingIndexPage parent
        self.assertIsInstance(
            meeting.get_parent().specific,
            MeetingIndexPage,
        )


class OrganizationIndexPageFactoryTest(TestCase):
    def test_organization_index_page_creation(self) -> None:
        # Create a OrganizationIndexPage instance
        organization_index_page = OrganizationIndexPageFactory.create()

        # Now test that it was created
        self.assertIsNotNone(organization_index_page)
        self.assertIsInstance(
            organization_index_page,
            OrganizationIndexPage,
        )

        # Test that the OrganizationIndexPage instance has a parent
        self.assertIsInstance(
            organization_index_page.get_parent().specific,
            CommunityPage,
        )


class OrganizationFactoryTest(TestCase):
    def test_organization_index_page_creation(self) -> None:
        # Create a Organization instance
        organization = OrganizationFactory.create()

        # Now test that it was created
        self.assertIsNotNone(organization)
        self.assertIsInstance(
            organization,
            Organization,
        )

        # Test that the Organization instance has a OrganizationIndexPage parent
        self.assertIsInstance(
            organization.get_parent().specific,
            OrganizationIndexPage,
        )


class TestMeetingIndexPageGetContext(TestCase):
    def setUp(self) -> None:
        self.request = RequestFactory().get("/")
        self.meeting_index = MeetingIndexPageFactory.create()
        self.child_meeting = MeetingFactory.build()
        self.meeting_index.add_child(instance=self.child_meeting)

    def test_get_context_includes_meetings(self) -> None:
        context = self.meeting_index.get_context(self.request)

        self.assertIn("meetings", context)
        self.assertIn(self.child_meeting, context["meetings"])

    def test_get_context_meetings_are_specific(self) -> None:
        context = self.meeting_index.get_context(self.request)

        for meeting in context["meetings"]:
            self.assertIsInstance(meeting, Meeting)


class TestMeetingGetContext(TestCase):
    def setUp(self) -> None:
        self.request = RequestFactory().get("/")
        self.meeting = MeetingFactory.create()

        self.child_quarterly_meeting = MeetingFactory.build(
            meeting_type=Meeting.MeetingTypeChoices.QUARTERLY_MEETING,
        )
        self.meeting.add_child(instance=self.child_quarterly_meeting)
        self.child_monthly_meeting = MeetingFactory.build(
            meeting_type=Meeting.MeetingTypeChoices.MONTHLY_MEETING,
        )
        self.meeting.add_child(instance=self.child_monthly_meeting)
        self.child_worship_group = MeetingFactory.build(
            meeting_type=Meeting.MeetingTypeChoices.WORSHIP_GROUP,
        )
        self.meeting.add_child(instance=self.child_worship_group)

    def test_meeting_get_context(self) -> None:
        context = self.meeting.get_context(self.request)

        self.assertIn("quarterly_meetings", context)
        self.assertIn("monthly_meetings", context)
        self.assertIn("worship_groups", context)

        self.assertEqual(
            list(context["quarterly_meetings"]),
            [self.child_quarterly_meeting],
        )
        self.assertEqual(
            list(context["monthly_meetings"]),
            [self.child_monthly_meeting],
        )
        self.assertEqual(
            list(context["worship_groups"]),
            [self.child_worship_group],
        )


class ContactQueryOptimizationTestCase(TestCase):
    """Test query optimization in contact pages to prevent N+1 queries.

    These tests verify that the get_context method in ContactBase properly
    prefetches all related content (articles, books, library items, memorials)
    and their nested relationships to avoid N+1 query patterns.

    Each test creates a contact with multiple related items, renders the template,
    and then asserts that accessing the relationships triggers zero additional queries.
    """

    def setUp(self) -> None:
        """Set up test fixtures for query optimization tests."""
        self.factory = RequestFactory()

        # Import models here and store as instance attributes to avoid circular imports
        # at module level while keeping them accessible to all test methods
        from library.models import LibraryItem, LibraryItemAuthor
        from magazine.models import (
            ArchiveArticle,
            ArchiveArticleAuthor,
            ArchiveIssue,
            DeepArchiveIndexPage,
            MagazineArticle,
            MagazineArticleAuthor,
            MagazineDepartment,
            MagazineDepartmentIndexPage,
            MagazineIndexPage,
            MagazineIssue,
        )
        from memorials.models import Memorial
        from store.models import Book, BookAuthor

        # Store model classes for use in tests
        self.MagazineArticle = MagazineArticle
        self.MagazineArticleAuthor = MagazineArticleAuthor
        self.MagazineIssue = MagazineIssue
        self.MagazineDepartment = MagazineDepartment
        self.MagazineDepartmentIndexPage = MagazineDepartmentIndexPage
        self.MagazineIndexPage = MagazineIndexPage
        self.DeepArchiveIndexPage = DeepArchiveIndexPage
        self.ArchiveArticle = ArchiveArticle
        self.ArchiveArticleAuthor = ArchiveArticleAuthor
        self.ArchiveIssue = ArchiveIssue
        self.Book = Book
        self.BookAuthor = BookAuthor
        self.LibraryItem = LibraryItem
        self.LibraryItemAuthor = LibraryItemAuthor
        self.Memorial = Memorial

    def test_person_with_related_content_query_optimization(self) -> None:
        """Test that Person pages with related content don't trigger N+1 queries."""
        from django.test.utils import override_settings

        person = PersonFactory.create()

        # Create magazine structure: MagazineIndexPage > DepartmentIndexPage > Department
        magazine_index = self.MagazineIndexPage(title="Magazine")
        PersonIndexPageFactory.create().add_child(instance=magazine_index)

        department_index = self.MagazineDepartmentIndexPage(title="Departments")
        magazine_index.add_child(instance=department_index)

        department = self.MagazineDepartment(title="Test Department")
        department_index.add_child(instance=department)

        # Create magazine issue
        issue = self.MagazineIssue(
            title="Test Issue 2024",
            publication_date="2024-01-01",
        )
        magazine_index.add_child(instance=issue)

        # Create 2 magazine articles authored by person
        for i in range(2):
            article = self.MagazineArticle(
                title=f"Test Article {i}",
                teaser="Test teaser",
                department=department,
            )
            issue.add_child(instance=article)
            self.MagazineArticleAuthor.objects.create(article=article, author=person)

        # Create 1 archive article with proper page hierarchy
        deep_archive_index = self.DeepArchiveIndexPage(title="Deep Archive")
        magazine_index.add_child(instance=deep_archive_index)

        archive_issue = self.ArchiveIssue(
            title="Archive Issue",
            internet_archive_identifier="test-archive-2020",
            publication_date="2020-01-01",
        )
        deep_archive_index.add_child(instance=archive_issue)

        archive_article = self.ArchiveArticle.objects.create(
            title="Archive Article",
            issue=archive_issue,
        )
        self.ArchiveArticleAuthor.objects.create(
            article=archive_article,
            author=person,
        )

        # Create 1 book authored by person
        book_index = PersonIndexPageFactory.create()
        book = self.Book(title="Test Book", price_usd=10.00)
        book_index.add_child(instance=book)
        self.BookAuthor.objects.create(book=book, author=person)

        # Create 1 library item
        library_index = PersonIndexPageFactory.create()
        library_item = self.LibraryItem(title="Test Library Item")
        library_index.add_child(instance=library_item)
        self.LibraryItemAuthor.objects.create(library_item=library_item, author=person)

        # Create 1 memorial minute for the person
        memorial_index = PersonIndexPageFactory.create()
        memorial = self.Memorial(
            title=f"Memorial for {person.title}",
            memorial_person=person,  # Link memorial to the person we're testing
            date_of_birth="1950-01-01",
            date_of_death="2020-01-01",
        )
        memorial_index.add_child(instance=memorial)

        # Get context (this should prefetch everything)
        request = self.factory.get("/")
        context = person.get_context(request)

        # Access all relationships - should trigger 0 additional queries
        with override_settings(DEBUG=True):
            from django.db import connection, reset_queries

            reset_queries()

            # Access magazine articles and their authors
            articles = list(context["page"].articles_authored.all())
            self.assertEqual(len(articles), 2)
            for article_link in articles:
                _ = article_link.article.title
                _ = article_link.article.department.title
                authors = list(article_link.article.authors.all())
                for author in authors:
                    _ = author.author.title

            # Access archive articles and their issues
            archive_articles = list(context["page"].archive_articles_authored.all())
            self.assertEqual(len(archive_articles), 1)
            for archive_link in archive_articles:
                _ = archive_link.article.title
                _ = archive_link.article.issue.title

            # Access books and their authors
            books = list(context["page"].books_authored.all())
            self.assertEqual(len(books), 1)
            for book_link in books:
                _ = book_link.book.title
                book_authors = list(book_link.book.authors.all())
                for author in book_authors:
                    _ = author.author.title

            # Access library items and their authors
            library_items = list(context["page"].library_items_authored.all())
            self.assertEqual(len(library_items), 1)
            for item_link in library_items:
                _ = item_link.library_item.title
                item_authors = list(item_link.library_item.authors.all())
                for author in item_authors:
                    _ = author.author.title

            # Access memorials and their persons
            memorials = list(context["page"].memorial_minute.all())
            self.assertEqual(len(memorials), 1)
            for memorial in memorials:
                _ = memorial.memorial_person.given_name
                _ = memorial.memorial_person.family_name

            # Test .count() method works (production bug fix)
            # Template uses {% if page.articles_authored.count %}
            # Previously failed with: TypeError: list.count() takes exactly one argument (0 given)
            self.assertIsInstance(context["page"].articles_authored.count(), int)
            self.assertIsInstance(
                context["page"].archive_articles_authored.count(),
                int,
            )
            self.assertIsInstance(context["page"].books_authored.count(), int)
            self.assertIsInstance(context["page"].library_items_authored.count(), int)
            self.assertIsInstance(context["page"].memorial_minute.count(), int)

            # Assert no additional queries were made
            query_count = len(connection.queries)
            self.assertEqual(
                query_count,
                0,
                f"Expected 0 queries after prefetch, but got {query_count}. "
                f"This indicates N+1 query regression.",
            )

    def test_meeting_with_related_content_query_optimization(self) -> None:
        """Test that Meeting pages with related content don't trigger N+1 queries."""
        from django.test.utils import override_settings

        meeting = MeetingFactory.create()

        # Create magazine structure
        magazine_index = self.MagazineIndexPage(title="Magazine")
        MeetingIndexPageFactory.create().add_child(instance=magazine_index)

        department_index = self.MagazineDepartmentIndexPage(title="Departments")
        magazine_index.add_child(instance=department_index)

        department = self.MagazineDepartment(title="Test Department")
        department_index.add_child(instance=department)

        # Create magazine issue
        issue = self.MagazineIssue(
            title="Test Issue 2024",
            publication_date="2024-01-01",
        )
        magazine_index.add_child(instance=issue)

        # Create 2 articles
        for i in range(2):
            article = self.MagazineArticle(
                title=f"Meeting Article {i}",
                teaser="Test teaser",
                department=department,
            )
            issue.add_child(instance=article)
            self.MagazineArticleAuthor.objects.create(article=article, author=meeting)

        # Create archive article with proper page hierarchy
        deep_archive_index = self.DeepArchiveIndexPage(title="Deep Archive")
        magazine_index.add_child(instance=deep_archive_index)

        archive_issue = self.ArchiveIssue(
            title="Archive Issue",
            internet_archive_identifier="test-archive-meeting-2020",
            publication_date="2020-01-01",
        )
        deep_archive_index.add_child(instance=archive_issue)

        archive_article = self.ArchiveArticle.objects.create(
            title="Archive Article",
            issue=archive_issue,
        )
        self.ArchiveArticleAuthor.objects.create(
            article=archive_article,
            author=meeting,
        )

        # Create book
        book_index = MeetingIndexPageFactory.create()
        book = self.Book(title="Meeting Book", price_usd=15.00)
        book_index.add_child(instance=book)
        self.BookAuthor.objects.create(book=book, author=meeting)

        # Create library item
        library_index = MeetingIndexPageFactory.create()
        library_item = self.LibraryItem(title="Meeting Library Item")
        library_index.add_child(instance=library_item)
        self.LibraryItemAuthor.objects.create(library_item=library_item, author=meeting)

        # Get context
        request = self.factory.get("/")
        context = meeting.get_context(request)

        # Access relationships - should trigger 0 queries
        with override_settings(DEBUG=True):
            from django.db import connection, reset_queries

            reset_queries()

            # Access all prefetched relationships including nested relationships
            articles = list(context["page"].articles_authored.all())
            for article_link in articles:
                _ = article_link.article.department.title
                for author in article_link.article.authors.all():
                    _ = author.author.title

            archive_articles = list(context["page"].archive_articles_authored.all())
            for archive_link in archive_articles:
                _ = archive_link.article.issue.title

            books = list(context["page"].books_authored.all())
            for book_link in books:
                for author in book_link.book.authors.all():
                    _ = author.author.title

            library_items = list(context["page"].library_items_authored.all())
            for item_link in library_items:
                for author in item_link.library_item.authors.all():
                    _ = author.author.title

            query_count = len(connection.queries)
            self.assertEqual(
                query_count,
                0,
                f"Expected 0 queries for Meeting, got {query_count}",
            )

    def test_organization_with_related_content_query_optimization(self) -> None:
        """Test that Organization pages with related content don't trigger N+1 queries."""
        from django.test.utils import override_settings

        organization = OrganizationFactory.create()

        # Create magazine structure
        magazine_index = self.MagazineIndexPage(title="Magazine")
        OrganizationIndexPageFactory.create().add_child(instance=magazine_index)

        department_index = self.MagazineDepartmentIndexPage(title="Departments")
        magazine_index.add_child(instance=department_index)

        department = self.MagazineDepartment(title="Test Department")
        department_index.add_child(instance=department)

        # Create magazine issue
        issue = self.MagazineIssue(
            title="Test Issue 2024",
            publication_date="2024-01-01",
        )
        magazine_index.add_child(instance=issue)

        # Create 2 articles
        for i in range(2):
            article = self.MagazineArticle(
                title=f"Org Article {i}",
                teaser="Test teaser",
                department=department,
            )
            issue.add_child(instance=article)
            self.MagazineArticleAuthor.objects.create(
                article=article,
                author=organization,
            )

        # Create archive article with proper page hierarchy
        deep_archive_index = self.DeepArchiveIndexPage(title="Deep Archive")
        magazine_index.add_child(instance=deep_archive_index)

        archive_issue = self.ArchiveIssue(
            title="Archive Issue",
            internet_archive_identifier="test-archive-org-2020",
            publication_date="2020-01-01",
        )
        deep_archive_index.add_child(instance=archive_issue)

        archive_article = self.ArchiveArticle.objects.create(
            title="Archive Article",
            issue=archive_issue,
        )
        self.ArchiveArticleAuthor.objects.create(
            article=archive_article,
            author=organization,
        )

        # Create book
        book_index = OrganizationIndexPageFactory.create()
        book = self.Book(title="Org Book", price_usd=20.00)
        book_index.add_child(instance=book)
        self.BookAuthor.objects.create(book=book, author=organization)

        # Create library item
        library_index = OrganizationIndexPageFactory.create()
        library_item = self.LibraryItem(title="Org Library Item")
        library_index.add_child(instance=library_item)
        self.LibraryItemAuthor.objects.create(
            library_item=library_item,
            author=organization,
        )

        # Get context
        request = self.factory.get("/")
        context = organization.get_context(request)

        # Access relationships - should trigger 0 queries
        with override_settings(DEBUG=True):
            from django.db import connection, reset_queries

            reset_queries()

            # Access all prefetched relationships including nested relationships
            articles = list(context["page"].articles_authored.all())
            for article_link in articles:
                _ = article_link.article.department.title
                for author in article_link.article.authors.all():
                    _ = author.author.title

            archive_articles = list(context["page"].archive_articles_authored.all())
            for archive_link in archive_articles:
                _ = archive_link.article.issue.title

            books = list(context["page"].books_authored.all())
            for book_link in books:
                for author in book_link.book.authors.all():
                    _ = author.author.title

            library_items = list(context["page"].library_items_authored.all())
            for item_link in library_items:
                for author in item_link.library_item.authors.all():
                    _ = author.author.title

            query_count = len(connection.queries)
            self.assertEqual(
                query_count,
                0,
                f"Expected 0 queries for Organization, got {query_count}",
            )


class ContactJsonLdEscapingTest(TestCase):
    def test_json_ld_escapes_script_breakout_and_is_valid_json(self) -> None:
        payload = '</script><script>alert("xss")</script>'
        organization = OrganizationFactory.create(title=payload)
        request = RequestFactory().get("/")
        request.user = AnonymousUser()

        response = organization.serve(request)
        response.render()

        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertFalse(
            '<script>alert("xss")</script>' in content,
            "Contact title rendered as unescaped script",
        )

        blocks = re.findall(
            r'<script type="application/ld\+json">(.*?)</script>',
            content,
            re.DOTALL,
        )
        parsed_blocks = [json.loads(block) for block in blocks]
        self.assertIn(payload, [block.get("name") for block in parsed_blocks])


def render_page(page: Page) -> str:
    request = RequestFactory().get("/")
    request.user = AnonymousUser()
    response = page.serve(request)
    response.render()
    return response.content.decode()


class BookFactory(ProductFactory):
    class Meta:
        model = Book


class ContactPageRenderingTest(TestCase):
    def test_meeting_page_renders_contact_details_and_related_content(self) -> None:
        meeting = MeetingFactory.create(
            title="Rendering Test Meeting",
            meeting_type="monthly_meeting",
            phone="555-0100",
            email="clerk@example.org",
            website="https://example.org/meeting",
            information_last_verified=datetime.date(2026, 1, 15),
        )
        MeetingAddress.objects.create(
            page=meeting,
            address_type="worship",
            street_address="123 Friendly Lane",
            locality="Portland",
        )
        MeetingWorshipTime.objects.create(
            meeting=meeting,
            worship_type="first_day_worship",
            worship_time="Sundays at 10am",
        )
        clerk = PersonFactory.create(given_name="Clara", family_name="Clerk")
        MeetingPresidingClerk.objects.create(meeting=meeting, person=clerk)
        for title, meeting_type in [
            ("Child Quarterly Meeting", "quarterly_meeting"),
            ("Child Monthly Meeting", "monthly_meeting"),
            ("Child Worship Group", "worship_group"),
        ]:
            meeting.add_child(
                instance=Meeting(title=title, meeting_type=meeting_type),
            )
        OnlineWorshipFactory.create(title="Zoom Worship", hosted_by=meeting)
        memorial = MemorialFactory.create(memorial_meeting=meeting)

        content = render_page(meeting)

        for expected in [
            "Rendering Test Meeting",
            'href="tel:555-0100"',
            'href="mailto:clerk@example.org"',
            'href="https://example.org/meeting"',
            "123 Friendly Lane",
            "Sundays at 10am",
            "Clara Clerk",
            'datetime="2026-01-15"',
            "Child Quarterly Meeting",
            "Child Monthly Meeting",
            "Child Worship Group",
            "Zoom Worship",
            f"View memorial for {memorial.memorial_person}",
        ]:
            with self.subTest(expected=expected):
                self.assertIn(expected, content)

    def test_person_page_renders_authored_works(self) -> None:
        person = PersonFactory.create(given_name="Ada", family_name="Author")
        unpublished_coauthor = PersonFactory.create(
            given_name="Una",
            family_name="Published",
        )
        unpublished_coauthor.unpublish()

        article = MagazineArticleFactory.create(title="Letters on Stillness")
        MagazineArticleAuthor.objects.create(article=article, author=person)

        deep_archive = Page.get_first_root_node().add_child(
            instance=DeepArchiveIndexPage(title="Deep Archive"),
        )
        archive_issue = deep_archive.add_child(
            instance=ArchiveIssue(
                title="Friends Bulletin 1950",
                publication_date=datetime.date(1950, 1, 1),
                internet_archive_identifier="friendsbulletin1950",
            ),
        )
        archive_article = ArchiveArticle.objects.create(
            title="Archived Reflections",
            issue=archive_issue,
            toc_page_number=3,
            pdf_page_number=5,
        )
        ArchiveArticleAuthor.objects.create(article=archive_article, author=person)

        book = BookFactory.create(title="Quiet Paths")
        BookAuthor.objects.create(book=book, author=person)
        BookAuthor.objects.create(book=book, author=unpublished_coauthor)

        library_item = LibraryItemFactory.create(title="Library Pamphlet")
        LibraryItemAuthor.objects.create(library_item=library_item, author=person)

        content = render_page(person)

        for expected in [
            "Letters on Stillness",
            "Archived Reflections",
            "?pdf_page_number=5",
            "Quiet Paths",
            f'content="{unpublished_coauthor}"',
            "Library Pamphlet",
        ]:
            with self.subTest(expected=expected):
                self.assertIn(expected, content)


class ReplaceNullStringsMigrationTest(TransactionTestCase):
    """NULLs saved before the NOT NULL change must not break publishing."""

    before = [("contact", "0011_contactpublicationstatistics")]
    after = [("contact", "0013_non_nullable_string_fields")]

    def setUp(self):
        MigrationExecutor(connection).migrate(self.before)

    def tearDown(self):
        executor = MigrationExecutor(connection)
        executor.migrate(executor.loader.graph.leaf_nodes())

    def test_nulls_in_rows_and_revisions_become_empty_strings(self):
        Locale.objects.get_or_create(language_code="en")
        try:
            root = Page.objects.get(depth=1)
        except Page.DoesNotExist:
            root = Page.add_root(title="Root", slug="root")
        meeting = root.add_child(instance=Meeting(title="Test meeting"))
        MeetingAddress.objects.create(page=meeting, address_type="mailing")
        MeetingWorshipTime.objects.create(meeting=meeting, worship_time="10am")
        revision = Meeting.objects.get(pk=meeting.pk).save_revision()

        # The current models write "", so force the NULLs that older data holds.
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE meeting SET website = NULL, email = NULL, phone = NULL, "
                "meeting_type = NULL",
            )
            cursor.execute(
                "UPDATE contact_meetingaddress SET locality = NULL, "
                "postal_code = NULL, country = NULL",
            )
            cursor.execute("UPDATE contact_meetingworshiptime SET worship_type = NULL")
        content = revision.content
        content.update(website=None, email=None, phone=None, meeting_type=None)
        content["addresses"][0].update(locality=None, postal_code=None, country=None)
        content["worship_times"][0]["worship_type"] = None
        Revision.objects.filter(pk=revision.pk).update(content=content)

        MigrationExecutor(connection).migrate(self.after)

        meeting = Meeting.objects.get(pk=meeting.pk)
        self.assertEqual(
            (meeting.website, meeting.email, meeting.phone, meeting.meeting_type),
            ("", "", "", ""),
        )
        address = meeting.addresses.get()
        self.assertEqual(
            (address.locality, address.postal_code, address.country),
            ("", "", ""),
        )
        self.assertEqual(meeting.worship_times.get().worship_type, "")

        revision.refresh_from_db()
        self.assertEqual(revision.content["website"], "")
        self.assertEqual(revision.content["addresses"][0]["country"], "")
        self.assertEqual(revision.content["worship_times"][0]["worship_type"], "")
        revision.publish()
