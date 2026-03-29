import datetime

from django.db import connection, reset_queries
from django.test import RequestFactory, TestCase, override_settings
from wagtail.models import Page, Site

from accounts.models import User
from contact.models import Person, PersonIndexPage
from home.models import HomePage
from magazine.factories import (
    MagazineArticleFactory,
    MagazineIndexPageFactory,
    MagazineIssueFactory,
)
from subscription.models import (
    Subscription,
)

from .models import (
    ArchiveArticle,
    ArchiveArticleAuthor,
    ArchiveIssue,
    DeepArchiveIndexPage,
    MagazineArticle,
    MagazineDepartment,
    MagazineDepartmentIndexPage,
    MagazineIndexPage,
    MagazineIssue,
    MagazineTagIndexPage,
)


class MagazineIndexPageTest(TestCase):
    def setUp(self) -> None:
        site_root = Page.objects.get(id=2)

        self.home_page = HomePage(title="Home")
        site_root.add_child(instance=self.home_page)

        Site.objects.all().update(root_page=self.home_page)

        self.magazine_index = MagazineIndexPage(
            title="Magazine",
        )
        self.home_page.add_child(instance=self.magazine_index)

        today = datetime.date.today()

        self.recent_magazine_issue = MagazineIssue(
            title="Issue 1",
            publication_date=today,
        )
        self.magazine_index.add_child(instance=self.recent_magazine_issue)

        number_of_archive_issues = 9
        self.archive_magazine_issues = []

        for i in range(number_of_archive_issues + 1):
            archive_days_ago = datetime.timedelta(days=181 + i)
            archive_magazine_issue = MagazineIssue(
                title=f"Archive issue {i}",
                publication_date=today - archive_days_ago,
            )

            self.magazine_index.add_child(instance=archive_magazine_issue)
            self.archive_magazine_issues.append(archive_magazine_issue)

    def test_get_sitemap_urls(self) -> None:
        """Validate the output of get_sitemap_urls."""

        expected_last_mod = None
        expected_location_contains = "/magazine/"

        sitemap_urls = self.magazine_index.get_sitemap_urls()

        self.assertEqual(len(sitemap_urls), 1)
        self.assertEqual(
            sitemap_urls[0]["lastmod"],
            expected_last_mod,
        )
        self.assertIn(
            expected_location_contains,
            sitemap_urls[0]["location"],
        )

    def test_get_context_recent_issues(self) -> None:
        """Validate the output of get_context."""

        mock_request = RequestFactory().get("/magazine/")

        context = self.magazine_index.get_context(mock_request)

        self.assertEqual(
            list(context["recent_issues"]),
            [self.recent_magazine_issue],
        )

    def test_get_context_archive_issues_without_page_number(self) -> None:
        """Make sure we get the first page when no page number is provided."""

        mock_request = RequestFactory().get("/magazine/")

        context = self.magazine_index.get_context(mock_request)

        number_of_issues_per_page = 8

        self.assertEqual(
            len(list(context["archive_issues"].page)),
            number_of_issues_per_page,
        )

        self.assertEqual(
            list(context["archive_issues"].page),
            self.archive_magazine_issues[:number_of_issues_per_page],
        )

    def test_get_context_archive_issues_with_page_number(self) -> None:
        """Make sure we get the second page of archive issues."""

        mock_request = RequestFactory().get("/magazine/?page=2")

        context = self.magazine_index.get_context(mock_request)

        number_of_issues_per_page = 8
        expected_number_of_issues_on_second_page = 2

        self.assertEqual(
            len(list(context["archive_issues"].page)),
            expected_number_of_issues_on_second_page,
        )

        self.assertEqual(
            list(context["archive_issues"].page),
            self.archive_magazine_issues[number_of_issues_per_page:],
        )

    def test_get_context_archive_issues_with_invalid_numeric_page_number(self) -> None:
        """Make sure we get the first page when an invalid page number is
        provided."""

        mock_request = RequestFactory().get("/magazine/?page=4")

        context = self.magazine_index.get_context(mock_request)  # type: ignore

        number_of_issues_per_page = 8

        self.assertEqual(
            len(list(context["archive_issues"].page)),
            number_of_issues_per_page,
        )

        self.assertEqual(
            list(context["archive_issues"].page),
            self.archive_magazine_issues[:number_of_issues_per_page],
        )

    def test_get_context_archive_issues_with_invalid_non_numeric_page_number(
        self,
    ) -> None:
        """Make sure we get the first page when an invalid page number is
        provided."""

        mock_request = RequestFactory().get("/magazine/?page=foo")

        context = self.magazine_index.get_context(mock_request)

        number_of_issues_per_page = 8

        self.assertEqual(
            len(list(context["archive_issues"].page)),
            number_of_issues_per_page,
        )

        self.assertEqual(
            list(context["archive_issues"].page),
            self.archive_magazine_issues[:number_of_issues_per_page],
        )


class MagazineIssueTest(TestCase):
    def setUp(self) -> None:
        site_root = Page.objects.get(id=2)

        self.home_page = HomePage(title="Home")
        site_root.add_child(instance=self.home_page)

        Site.objects.all().update(root_page=self.home_page)

        self.magazine_index = MagazineIndexPage(title="Magazine")
        self.home_page.add_child(instance=self.magazine_index)

        # Magazine Issues
        self.recent_magazine_issue = MagazineIssue(
            title="Issue 1",
            publication_date=datetime.date.today(),
        )
        self.archive_magazine_issue = MagazineIssue(
            title="Issue 2",
            publication_date=datetime.date.today() - datetime.timedelta(days=181),
        )
        self.magazine_index.add_child(instance=self.recent_magazine_issue)
        self.magazine_index.add_child(instance=self.archive_magazine_issue)

        # Magazine Departments
        self.magazine_department_index = MagazineDepartmentIndexPage(
            title="Departments",
        )
        self.magazine_index.add_child(instance=self.magazine_department_index)
        self.magazine_department_one = MagazineDepartment(
            title="Department 1",
        )
        self.magazine_department_two = MagazineDepartment(
            title="Department 2",
        )
        self.magazine_department_index.add_child(instance=self.magazine_department_one)
        self.magazine_department_index.add_child(instance=self.magazine_department_two)

        # Magazine Articles
        self.magazine_article_one = self.recent_magazine_issue.add_child(
            instance=MagazineArticle(
                title="Article 1",
                department=self.magazine_department_two,
                is_featured=True,
            ),
        )
        self.magazine_article_two = self.recent_magazine_issue.add_child(
            instance=MagazineArticle(
                title="Article 2",
                department=self.magazine_department_one,
                is_featured=False,
            ),
        )

    def test_featured_articles(self) -> None:
        """Test that the featured_articles property returns the correct
        articles."""
        self.assertEqual(
            list(self.recent_magazine_issue.featured_articles),
            [self.magazine_article_one],
        )

    def test_articles_by_department(self) -> None:
        """Test that the articles_by_department property returns the correct
        articles."""
        self.assertEqual(
            list(self.recent_magazine_issue.articles_by_department),
            [
                self.magazine_article_two,
                self.magazine_article_one,
            ],
        )

    def test_publication_end_date(self) -> None:
        """Test that the publication_end_date property returns the correct
        date."""
        self.assertEqual(
            self.recent_magazine_issue.publication_end_date,
            datetime.date.today() + datetime.timedelta(days=31),
        )

    def test_get_sitemap_urls(self) -> None:
        """Validate the output of get_sitemap_urls."""

        expected_last_mod = None
        expected_location_contains = "/magazine/issue-1/"

        sitemap_urls = self.recent_magazine_issue.get_sitemap_urls()

        self.assertEqual(len(sitemap_urls), 1)
        self.assertEqual(
            sitemap_urls[0]["lastmod"],
            expected_last_mod,
        )
        self.assertIn(
            expected_location_contains,
            sitemap_urls[0]["location"],
        )

    def test_is_public_access(self) -> None:
        """Test that the is_public_access property returns the correct
        boolean."""
        self.assertFalse(self.recent_magazine_issue.is_public_access)
        self.assertTrue(self.archive_magazine_issue.is_public_access)


class MagazineTagIndexPageTest(TestCase):
    def setUp(self) -> None:
        self.factory = RequestFactory()
        self.root = Site.objects.get(is_default_site=True).root_page

        # Create a MagazineIndexPage
        self.magazine_index = MagazineIndexPage(title="Magazine")
        self.root.add_child(instance=self.magazine_index)

        # Create a page of MagazineTagIndexPage type
        self.magazine_tag_index_page = MagazineTagIndexPage(title="Tag Index")
        self.magazine_index.add_child(instance=self.magazine_tag_index_page)

        # Create a MagazineDepartmentIndexPage
        self.department_index = MagazineDepartmentIndexPage(title="Departments")
        self.magazine_index.add_child(instance=self.department_index)

        # Create some MagazineDepartments
        self.department1 = MagazineDepartment(
            title="Department 1",
        )
        self.department2 = MagazineDepartment(
            title="Department 2",
        )

        self.department_index.add_child(instance=self.department1)
        self.department_index.add_child(instance=self.department2)

        # Create some MagazineArticles with tags
        self.article1 = MagazineArticle(
            title="Article 1",
            department=self.department1,
        )
        self.article2 = MagazineArticle(
            title="Article 2",
            department=self.department2,
        )
        self.article3 = MagazineArticle(
            title="Article 3",
            department=self.department2,
        )

        python_tag = "Python"
        django_tag = "Django"

        self.article1.tags.add(python_tag)
        self.article2.tags.add(python_tag)
        self.article3.tags.add(django_tag)

        self.magazine_index.add_child(instance=self.article1)
        self.magazine_index.add_child(instance=self.article2)
        self.magazine_index.add_child(instance=self.article3)

        MagazineArticle.objects.all()

    def test_get_context(self) -> None:
        # Create a mock request with 'tag' as a GET parameter
        request = self.factory.get("/magazine/tag-index/?tag=Python")

        # Call the get_context method
        context = self.magazine_tag_index_page.get_context(request)

        # Check that the context includes the articles tagged with 'Python'
        self.assertEqual(
            list(context["articles"]),
            [self.article1, self.article2],
        )

        # Check that the context doesn't include articles tagged with 'Django'
        self.assertNotIn(
            self.article3,
            context["articles"],
        )


class MagazineDepartmentIndexPageTest(TestCase):
    def setUp(self) -> None:
        self.factory = RequestFactory()
        self.root = Site.objects.get(is_default_site=True).root_page

        # Create a MagazineIndexPage
        self.magazine_index = MagazineIndexPage(title="Magazine")
        self.root.add_child(instance=self.magazine_index)

        # Create a MagazineDepartmentIndexPage
        self.department_index = MagazineDepartmentIndexPage(title="Department Index")
        self.magazine_index.add_child(instance=self.department_index)

        # Create some MagazineDepartments
        self.department1 = MagazineDepartment(title="Department 1")
        self.department2 = MagazineDepartment(title="Department 2")

        self.department_index.add_child(instance=self.department1)
        self.department_index.add_child(instance=self.department2)

    def test_get_context(self) -> None:
        # Create a mock request
        request = self.factory.get("/")

        # Call the get_context method
        context = self.department_index.get_context(request)

        # Check that the context includes the departments
        self.assertQuerySetEqual(  # type: ignore
            context["departments"],
            MagazineDepartment.objects.all(),
            transform=lambda x: x,  # Transform the objects to compare them directly
            ordered=False,  # The order of the results is not important
        )


class MagazineDepartmentTest(TestCase):
    def test_magazine_department_str(self) -> None:
        """Test that the MagazineDepartment __str__ method returns the correct
        string."""
        department = MagazineDepartment(title="Department 1")
        self.assertEqual(str(department), "Department 1")

    def test_magazine_department_autocomplete_label(self) -> None:
        """Test that the MagazineDepartment autocomplete_label property returns
        the correct string."""
        department = MagazineDepartment(title="Department 1")
        self.assertEqual(department.autocomplete_label(), "Department 1")


class MagazineArticleTest(TestCase):
    def setUp(self) -> None:
        self.admin_user = User.objects.create_superuser(
            email="admin@email.com",
            password="password",  # nosec - Banned password
        )
        self.regular_user = User.objects.create_user(
            email="regular@email.com",
            password="password",  # nosec - Banned password
        )
        self.subscriber_user = User.objects.create_user(
            email="subscriber@email.com",
            password="password",  # nosec - Banned password
        )
        self.subscription = Subscription.objects.create(
            user=self.subscriber_user,
            expiration_date=datetime.date.today() + datetime.timedelta(days=365),
        )

        site_root = Page.objects.get(id=2)

        self.home_page = HomePage(title="Home")
        site_root.add_child(instance=self.home_page)

        Site.objects.all().update(root_page=self.home_page)

        self.magazine_index = MagazineIndexPage(
            title="Magazine",
        )
        self.home_page.add_child(instance=self.magazine_index)

        today = datetime.date.today()

        # Magazine Issues
        self.recent_magazine_issue = MagazineIssue(
            title="Issue 1",
            publication_date=today,
        )
        self.archive_magazine_issue = MagazineIssue(
            title="Issue 2",
            publication_date=today - datetime.timedelta(days=181),
        )
        self.magazine_index.add_child(instance=self.recent_magazine_issue)
        self.magazine_index.add_child(instance=self.archive_magazine_issue)

        # Magazine Departments
        self.magazine_department_index = MagazineDepartmentIndexPage(
            title="Departments",
        )
        self.magazine_index.add_child(instance=self.magazine_department_index)

        self.magazine_department = MagazineDepartment(
            title="Department 1",
        )
        self.magazine_department_index.add_child(instance=self.magazine_department)

        # Magazine Articles
        self.recent_magazine_article = MagazineArticle(
            title="Article 1",
            department=self.magazine_department,
        )
        self.archive_magazine_article = MagazineArticle(
            title="Article 2",
            department=self.magazine_department,
        )
        self.recent_magazine_issue.add_child(instance=self.recent_magazine_article)
        self.archive_magazine_issue.add_child(instance=self.archive_magazine_article)

    def test_get_sitemap_urls(self) -> None:
        """Validate the output of get_sitemap_urls."""

        expected_last_mod = None
        expected_location_contains = "/magazine/issue-1/article-1/"

        sitemap_urls = self.recent_magazine_article.get_sitemap_urls()

        self.assertEqual(len(sitemap_urls), 1)
        self.assertEqual(
            sitemap_urls[0]["lastmod"],
            expected_last_mod,
        )
        self.assertIn(
            expected_location_contains,
            sitemap_urls[0]["location"],
        )

    def test_is_public_access(self) -> None:
        """Test that the is_public_access property returns the correct
        boolean."""
        self.assertFalse(self.recent_magazine_article.is_public_access)
        self.assertTrue(self.archive_magazine_article.is_public_access)

    def test_recent_get_context_anonymous(self) -> None:
        """Test that the get_context method returns the correct context."""
        mock_request = RequestFactory().get("/magazine/issue-1/article-1/")
        mock_request.user = self.regular_user
        context = self.recent_magazine_article.get_context(mock_request)

        self.assertEqual(
            context["user_can_view_full_article"],
            False,
        )

    def test_recent_get_context_registered(self) -> None:
        """Test that the get_context method returns the correct context."""
        mock_request = RequestFactory().get("/magazine/issue-1/article-1/")
        mock_request.user = self.regular_user
        context = self.recent_magazine_article.get_context(mock_request)

        self.assertEqual(
            context["user_can_view_full_article"],
            False,
        )

    def test_recent_get_context_subscriber(self) -> None:
        """Test that the get_context method returns the correct context."""
        mock_request = RequestFactory().get("/magazine/issue-1/article-1/")
        mock_request.user = self.subscriber_user
        context = self.recent_magazine_article.get_context(mock_request)

        self.assertEqual(
            context["user_can_view_full_article"],
            True,
        )

    def test_recent_get_context_admin(self) -> None:
        """Test that the get_context method returns the correct context."""
        mock_request = RequestFactory().get("/magazine/issue-1/article-1/")
        mock_request.user = self.admin_user
        context = self.recent_magazine_article.get_context(mock_request)

        self.assertEqual(
            context["user_can_view_full_article"],
            True,
        )

    def test_archive_get_context_anonymous(self) -> None:
        """Test that the get_context method returns the correct context."""
        mock_request = RequestFactory().get("/magazine/issue-2/article-2/")
        mock_request.user = self.regular_user
        context = self.archive_magazine_article.get_context(mock_request)

        self.assertEqual(
            context["user_can_view_full_article"],
            True,
        )

    def test_archive_get_context_registered(self) -> None:
        """Test that the get_context method returns the correct context."""
        mock_request = RequestFactory().get("/magazine/issue-2/article-2/")
        mock_request.user = self.regular_user
        context = self.archive_magazine_article.get_context(mock_request)

        self.assertEqual(
            context["user_can_view_full_article"],
            True,
        )

    def test_archive_get_context_subscriber(self) -> None:
        """Test that the get_context method returns the correct context."""
        mock_request = RequestFactory().get("/magazine/issue-2/article-2/")
        mock_request.user = self.subscriber_user
        context = self.archive_magazine_article.get_context(mock_request)

        self.assertEqual(
            context["user_can_view_full_article"],
            True,
        )

    def test_archive_get_context_admin(self) -> None:
        """Test that the get_context method returns the correct context."""
        mock_request = RequestFactory().get("/magazine/issue-2/article-2/")
        mock_request.user = self.admin_user
        context = self.archive_magazine_article.get_context(mock_request)

        self.assertEqual(
            context["user_can_view_full_article"],
            True,
        )


class DeepArchiveIndexPageTest(TestCase):
    def setUp(self) -> None:
        self.factory = RequestFactory()
        self.root = Site.objects.get(is_default_site=True).root_page

        # Create a MagazineIndexPage
        self.magazine_index = MagazineIndexPage(title="Magazine")
        self.root.add_child(instance=self.magazine_index)

        # Create a DeepArchiveIndexPage
        self.deep_archive_index = DeepArchiveIndexPage(title="Deep Archive Index")
        self.magazine_index.add_child(instance=self.deep_archive_index)

        self.publication_years = list(range(1920, 1970))

        self.archive_issues = []

        for year in self.publication_years:
            archive_issue = ArchiveIssue(
                title=f"Archive Issue {year}",  # type: ignore
                internet_archive_identifier=f"archive-issue-{year}",  # type: ignore
                publication_date=datetime.date(year, 1, 1),  # type: ignore
            )
            self.deep_archive_index.add_child(instance=archive_issue)
            self.archive_issues.append(archive_issue)

    def test_get_context(self) -> None:
        # Create a mock request
        request = self.factory.get("/")

        # Call the get_context method
        context = self.deep_archive_index.get_context(request)

        archive_items_per_page = 12

        # Check that the context includes the archive issues
        self.assertQuerySetEqual(  # type: ignore
            context["archive_issues"].page,
            self.archive_issues[:archive_items_per_page],
            transform=lambda x: x,  # Transform the objects to compare them directly
            ordered=False,  # The order of the results is not important
        )

        # Check that the context includes the publication years
        self.assertEqual(
            list(context["publication_years"]),
            self.publication_years,
        )

    def test_get_context_with_page_number(self) -> None:
        # Create a mock request with 'page' as a GET parameter
        request = self.factory.get("/?page=2")

        # Call the get_context method
        context = self.deep_archive_index.get_context(request)

        archive_items_per_page = 12

        self.assertEqual(
            len(list(context["archive_issues"].page)),
            archive_items_per_page,
        )

        # Calculate the start and end indices for slicing the archive issues list
        start_index = archive_items_per_page
        end_index = archive_items_per_page * 2

        # Extract the items that should be on the second page
        expected_issues = self.archive_issues[start_index:end_index]

        # Now we're not just checking the length, but also the actual issues
        self.assertQuerySetEqual(
            context["archive_issues"].page,
            expected_issues,
            transform=lambda x: x,  # Transform the objects to compare them directly
            ordered=False,  # The order of the results is not important
        )


class TestMagazineIndexPageFactory(TestCase):
    def test_magazine_index_page_factory(self) -> None:
        """Test that the MagazineIndexPageFactory creates a MagazineIndexPage
        instance."""
        magazine_index_page = MagazineIndexPageFactory.create()
        self.assertIsInstance(magazine_index_page, MagazineIndexPage)

        self.assertIsInstance(
            magazine_index_page.get_parent().specific,
            HomePage,
        )


class TestMagazineIssueFactory(TestCase):
    def test_magazine_issue_factory(self) -> None:
        """Test that the MagazineIssueFactory creates a MagazineIssue
        instance."""
        magazine_issue = MagazineIssueFactory.create()
        self.assertIsInstance(magazine_issue, MagazineIssue)

        self.assertIsInstance(
            magazine_issue.get_parent().specific,
            MagazineIndexPage,
        )


class MagazineArticleParentIssueTest(TestCase):
    def setUp(self) -> None:
        self.issue = MagazineIssueFactory.create()
        self.article = MagazineArticleFactory.create(parent=self.issue)

    def test_parent_issue_returns_magazine_issue(self) -> None:
        """parent_issue returns the correct MagazineIssue via DB lookup."""
        self.assertIsInstance(self.article.parent_issue, MagazineIssue)
        self.assertEqual(self.article.parent_issue.pk, self.issue.pk)

    def test_parent_issue_uses_annotated_value_when_set(self) -> None:
        """parent_issue returns _parent_page directly when pre-populated
        by annotate_parent_page(), without hitting the database."""
        self.article._parent_page = self.issue
        with self.assertNumQueries(0):
            result = self.article.parent_issue
        self.assertEqual(result.pk, self.issue.pk)

    def test_parent_issue_falls_back_to_db_when_not_annotated(self) -> None:
        """parent_issue queries the DB when _parent_page is not set."""
        # Ensure _parent_page is absent (default state, no annotation)
        self.assertFalse(hasattr(self.article, "_parent_page"))
        result = self.article.parent_issue
        self.assertIsInstance(result, MagazineIssue)
        self.assertEqual(result.pk, self.issue.pk)


class ArchiveIssueQueryOptimizationTestCase(TestCase):
    """Test that ArchiveIssue.get_context() optimizes queries to avoid N+1.

    Validates that accessing article.archive_authors.all and archive_author.author
    does not trigger per-article or per-author queries when the queryset is
    properly prefetched in get_context().
    """

    def setUp(self) -> None:
        """Create test data: 1 archive issue with 3 articles, each with 2 authors."""
        self.factory = RequestFactory()
        self.root = Site.objects.get(is_default_site=True).root_page

        # Create magazine index and deep archive index pages
        self.magazine_index = MagazineIndexPage(title="Magazine")
        self.root.add_child(instance=self.magazine_index)

        self.deep_archive_index = DeepArchiveIndexPage(title="Deep Archive")
        self.magazine_index.add_child(instance=self.deep_archive_index)

        # Create a person index page for author pages
        self.person_index = PersonIndexPage(title="People")
        self.root.add_child(instance=self.person_index)

        # Create an archive issue
        self.archive_issue = ArchiveIssue(
            title="Test Archive Issue",
            internet_archive_identifier="test-issue-123",
            publication_date=datetime.date(1950, 1, 1),
        )
        self.deep_archive_index.add_child(instance=self.archive_issue)

        # Create 6 author pages (Person instances)
        self.authors = []
        for i in range(6):
            author = Person(
                title=f"Author {i}",
                given_name=f"Given{i}",
                family_name=f"Family{i}",
            )
            self.person_index.add_child(instance=author)
            self.authors.append(author)

        # Create 3 archive articles with 2 authors each
        self.articles = []
        for article_num in range(3):
            article = ArchiveArticle(
                title=f"Test Article {article_num}",
                issue=self.archive_issue,
                toc_page_number=article_num + 1,
                pdf_page_number=article_num + 1,
            )
            article.save()
            self.articles.append(article)

            # Add 2 authors to each article
            for author_offset in range(2):
                author_index = article_num * 2 + author_offset
                ArchiveArticleAuthor.objects.create(
                    article=article,
                    author=self.authors[author_index],
                )

    @override_settings(DEBUG=True)
    def test_get_context_prefetches_authors(self) -> None:
        """Verify that get_context() prefetches authors to prevent N+1 queries.

        After calling get_context(), accessing article.archive_authors.all and
        archive_author.author should not trigger additional queries.
        """
        request = self.factory.get("/")

        # Reset queries to get a clean count
        reset_queries()

        # Get the context with prefetched data
        context = self.archive_issue.get_context(request)
        articles = context["archive_articles"]

        # Record query count after get_context
        queries_after_context = len(connection.queries)

        # Now access archive_authors and author for all articles
        # This should NOT trigger additional queries if prefetch worked
        for article in articles:
            for archive_author in article.archive_authors.all():
                # Access author fields that would normally trigger queries
                _ = archive_author.author.title
                _ = archive_author.author.live

        # Record final query count
        queries_after_access = len(connection.queries)

        # Assert NO additional queries were made when accessing authors
        additional_queries = queries_after_access - queries_after_context

        self.assertEqual(
            additional_queries,
            0,
            f"Expected 0 additional queries, but got {additional_queries}. "
            f"Prefetch did not prevent N+1 queries.",
        )

    @override_settings(DEBUG=True)
    def test_total_query_count_is_reasonable(self) -> None:
        """Verify total query count is independent of article/author count.

        The total query count should be low (≤5) and not scale with the number
        of articles or authors, confirming the optimization is effective.
        """
        request = self.factory.get("/")

        # Reset queries
        reset_queries()

        # Get context and access all data
        context = self.archive_issue.get_context(request)
        articles = context["archive_articles"]

        # Access all article and author data
        for article in articles:
            for archive_author in article.archive_authors.all():
                _ = archive_author.author.title
                _ = archive_author.author.live

        total_queries = len(connection.queries)

        # With proper prefetching, we should have:
        # 1-2 queries for page/issue data
        # 1 query for articles
        # 1 query for archive_authors
        # 1 query for author pages
        # Total should be ≤ 5 regardless of data volume
        self.assertLessEqual(
            total_queries,
            5,
            f"Expected ≤5 queries with prefetch optimization, but got {total_queries}. "
            f"Queries: {[q['sql'] for q in connection.queries]}",
        )
