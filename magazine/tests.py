import datetime
from contextlib import contextmanager
from unittest.mock import patch

from django.core.cache import cache, caches
from django.core.management import call_command
from django.db import connection, reset_queries
from django.http import HttpResponse
from django.test import RequestFactory, SimpleTestCase, TestCase, override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone
from wagtail.images import get_image_model
from wagtail.images.models import Rendition
from wagtail.images.tests.utils import get_test_image_file
from wagtail.models import Page, Site
from wagtail.search.backends import get_search_backend

from accounts.models import User
from common.cache_queries import (
    DATABASE_CACHES,
    django_cache_queries,
    django_cache_reads,
)
from common.fake_content import image_block
from common.renditions import BODY_IMAGE_RENDITION_SPEC
from contact.models import Person, PersonIndexPage
from home.models import HomePage
from magazine.factories import (
    ArchiveIssueFactory,
    MagazineArticleFactory,
    MagazineIndexPageFactory,
    MagazineIssueFactory,
)
from subscription.models import (
    Subscription,
)

from .models import (
    COVER_IMAGE_RENDITION_SPECS,
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
    get_archive_threshold_date,
)


class ArchiveThresholdDateTest(SimpleTestCase):
    def test_threshold_advances_with_current_date(self) -> None:
        """The threshold is recomputed on each call, not frozen at import."""
        first_day = datetime.date(2026, 1, 1)
        later_day = datetime.date(2026, 3, 1)

        with patch("django.utils.timezone.localdate", return_value=first_day):
            self.assertEqual(
                get_archive_threshold_date(),
                first_day - datetime.timedelta(days=180),
            )

        with patch("django.utils.timezone.localdate", return_value=later_day):
            self.assertEqual(
                get_archive_threshold_date(),
                later_day - datetime.timedelta(days=180),
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

        today = timezone.localdate()

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

    def test_get_context_recent_issues_moves_to_archive_as_date_advances(
        self,
    ) -> None:
        """A recent issue moves to the archive once the current date passes the
        threshold, without a process restart."""
        mock_request = RequestFactory().get("/magazine/")
        later_day = self.recent_magazine_issue.publication_date + datetime.timedelta(
            days=181,
        )

        with patch("django.utils.timezone.localdate", return_value=later_day):
            context = self.magazine_index.get_context(mock_request)

        self.assertEqual(list(context["recent_issues"]), [])
        self.assertIn(
            self.recent_magazine_issue,
            list(context["archive_issues"].page),
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
            publication_date=timezone.localdate(),
        )
        self.archive_magazine_issue = MagazineIssue(
            title="Issue 2",
            publication_date=timezone.localdate() - datetime.timedelta(days=181),
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
            timezone.localdate() + datetime.timedelta(days=31),
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

    def test_is_public_access_changes_as_date_advances(self) -> None:
        """An issue becomes public once the current date passes the threshold,
        without a process restart."""
        publication_date = self.recent_magazine_issue.publication_date

        with patch(
            "django.utils.timezone.localdate",
            return_value=publication_date + datetime.timedelta(days=180),
        ):
            self.assertFalse(self.recent_magazine_issue.is_public_access)

        with patch(
            "django.utils.timezone.localdate",
            return_value=publication_date + datetime.timedelta(days=181),
        ):
            self.assertTrue(self.recent_magazine_issue.is_public_access)


class MagazineTagIndexPageTest(TestCase):
    def setUp(self) -> None:
        Site.clear_site_root_paths_cache()
        self.addCleanup(Site.clear_site_root_paths_cache)
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

    def test_tagged_articles_are_h2_under_the_page_h1(self) -> None:
        # The list sits directly under the page's <h1>, so an <h3> title
        # would skip a heading level.
        response = self.client.get(f"{self.magazine_tag_index_page.url}?tag=Python")
        html = response.content.decode()

        self.assertEqual(response.status_code, 200)
        self.assertRegex(
            html,
            r'<h2 class="card-title">\s*<a href="[^"]*">\s*Article 1',
        )
        self.assertNotIn('<h3 class="card-title">', html)


class MagazineArticleSummaryHeadingTest(TestCase):
    """The article card's title level follows the page it is listed on."""

    def setUp(self) -> None:
        root = Site.objects.get(is_default_site=True).root_page
        magazine_index = MagazineIndexPage(title="Magazine")
        root.add_child(instance=magazine_index)
        department_index = MagazineDepartmentIndexPage(title="Departments")
        magazine_index.add_child(instance=department_index)
        self.department = MagazineDepartment(title="Heading Department")
        department_index.add_child(instance=self.department)
        self.article = MagazineArticle(
            title="Heading Level Article",
            department=self.department,
        )
        magazine_index.add_child(instance=self.article)

    def test_department_page_keeps_h3_under_its_articles_h2(self) -> None:
        response = self.client.get(self.department.url)
        html = response.content.decode()

        self.assertEqual(response.status_code, 200)
        self.assertIn('<h2 id="articles-heading">', html)
        self.assertRegex(
            html,
            r'<h3 class="card-title">\s*<a href="[^"]*">\s*Heading Level Article',
        )

    def test_search_result_is_h2_under_the_search_h1(self) -> None:
        get_search_backend().add(self.article)

        response = self.client.get(reverse("search"), {"query": "Heading Level"})
        html = response.content.decode()

        self.assertTemplateUsed(response, "search/magazine_article.html")
        self.assertRegex(
            html,
            r'<h2 class="card-title">\s*<a href="[^"]*">\s*Heading Level Article',
        )
        self.assertNotIn('<h3 class="card-title">', html)


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

    def test_get_context(self) -> None:
        """Test that get_context returns articles for the department."""
        # Set up page hierarchy
        site_root = Page.objects.get(id=2)
        home_page = HomePage(title="Home")
        site_root.add_child(instance=home_page)
        Site.objects.all().update(root_page=home_page)

        magazine_index = MagazineIndexPage(title="Magazine")
        home_page.add_child(instance=magazine_index)

        magazine_issue = MagazineIssue(
            title="Test Issue",
            publication_date=timezone.localdate(),
        )
        magazine_index.add_child(instance=magazine_issue)

        department_index = MagazineDepartmentIndexPage(title="Departments")
        magazine_index.add_child(instance=department_index)

        department = MagazineDepartment(title="Test Department")
        department_index.add_child(instance=department)
        other_department = MagazineDepartment(title="Other Department")
        department_index.add_child(instance=other_department)

        # Create some articles
        article1 = MagazineArticle(
            title="Article 1",
            department=department,
        )
        article2 = MagazineArticle(
            title="Article 2",
            department=department,
        )
        other_article = MagazineArticle(
            title="Article 3",
            department=other_department,
        )
        magazine_issue.add_child(instance=article1)
        magazine_issue.add_child(instance=article2)
        magazine_issue.add_child(instance=other_article)

        factory = RequestFactory()
        request = factory.get("/")
        context = department.get_context(request)

        self.assertIn("articles", context)
        articles = list(context["articles"])
        self.assertEqual(len(articles), 2)
        self.assertCountEqual(
            [article.pk for article in articles],
            [article1.pk, article2.pk],
        )


class MagazineArticleTest(TestCase):
    def setUp(self) -> None:
        Site.clear_site_root_paths_cache()
        self.addCleanup(Site.clear_site_root_paths_cache)
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
            expiration_date=timezone.localdate() + datetime.timedelta(days=365),
        )

        site_root = Page.objects.get(id=2)

        self.home_page = HomePage(title="Home")
        site_root.add_child(instance=self.home_page)

        Site.objects.all().update(root_page=self.home_page)

        self.magazine_index = MagazineIndexPage(
            title="Magazine",
        )
        self.home_page.add_child(instance=self.magazine_index)

        today = timezone.localdate()

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

    def test_public_body_images_are_bulk_prefetched_on_cold_render(self) -> None:
        images = [
            get_image_model().objects.create(
                title=f"Article image {index}",
                file=get_test_image_file(filename=f"article-{index}.gif"),
            )
            for index in range(4)
        ]
        self.archive_magazine_article.body = [image_block(image) for image in images]
        self.archive_magazine_article.save()
        cache.clear()
        with CaptureQueriesContext(connection) as queries:
            response = self.client.get(self.archive_magazine_article.url)

        self.assertEqual(response.status_code, 200)
        selects = [
            query
            for query in queries
            if "wagtailimages_rendition" in query["sql"]
            and query["sql"].lstrip().upper().startswith("SELECT")
        ]
        self.assertLessEqual(len(selects), 2)
        for image in images:
            self.assertContains(
                response,
                image.get_rendition(BODY_IMAGE_RENDITION_SPEC).url,
            )

    def test_restricted_body_does_not_prefetch_renditions(self) -> None:
        request = RequestFactory().get("/")
        request.user = self.regular_user
        with patch("magazine.models._prefetch_streamfield_renditions") as prefetch:
            context = self.recent_magazine_article.get_context(request)
        self.assertFalse(context["user_can_view_full_article"])
        prefetch.assert_not_called()

    def test_missing_body_image_does_not_prevent_article_rendering(self) -> None:
        image_model = get_image_model()
        missing = image_model.objects.create(
            title="Missing image",
            file=get_test_image_file(filename="missing-article.gif"),
        )
        healthy = image_model.objects.create(
            title="Available image",
            file=get_test_image_file(filename="available-article.gif"),
        )
        self.archive_magazine_article.body = [
            image_block(missing),
            image_block(healthy),
        ]
        self.archive_magazine_article.save()
        missing.file.close()
        missing.file.storage.delete(missing.file.name)
        cache.clear()

        response = self.client.get(self.archive_magazine_article.url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "not-found")
        rendition = healthy.renditions.get(filter_spec=BODY_IMAGE_RENDITION_SPEC)
        self.assertContains(response, rendition.url)

    def test_body_image_read_error_uses_fallback_without_retry(self) -> None:
        image_model = get_image_model()
        unreadable = image_model.objects.create(
            title="Unreadable image",
            file=get_test_image_file(filename="unreadable-article.gif"),
        )
        healthy = image_model.objects.create(
            title="Readable image",
            file=get_test_image_file(filename="readable-article.gif"),
        )
        self.archive_magazine_article.body = [
            image_block(unreadable),
            image_block(healthy),
        ]
        self.archive_magazine_article.save()
        cache.clear()
        original_open_file = image_model.open_file
        attempts = []

        class FailingReader:
            def read(self):
                raise OSError

        @contextmanager
        def open_file(image):
            if image.pk == unreadable.pk:
                attempts.append(image.pk)
                with original_open_file(image):
                    yield FailingReader()
            else:
                with original_open_file(image) as source:
                    yield source

        with patch.object(image_model, "open_file", open_file):
            response = self.client.get(self.archive_magazine_article.url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "not-found")
        self.assertEqual(attempts, [unreadable.pk])
        rendition = healthy.renditions.get(filter_spec=BODY_IMAGE_RENDITION_SPEC)
        self.assertContains(response, rendition.url)

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


class ArchiveIssueFactoryTest(TestCase):
    def test_creates_issue_with_saved_table_of_contents(self) -> None:
        issue = ArchiveIssueFactory.create(archive_articles=3)

        self.assertIsInstance(issue.get_parent().specific, DeepArchiveIndexPage)
        self.assertEqual(issue.archive_articles.count(), 3)
        self.assertIn(f"{issue.publication_date:%Y}", issue.title)

    def test_second_issue_reuses_the_deep_archive(self) -> None:
        first = ArchiveIssueFactory.create()
        second = ArchiveIssueFactory.create()

        self.assertEqual(first.get_parent(), second.get_parent())
        self.assertGreaterEqual(second.archive_articles.count(), 2)


def _point_site_at_home() -> HomePage:
    home = HomePage.objects.get()
    Site.objects.all().delete()
    Site.objects.create(
        hostname="testserver",
        root_page=home,
        is_default_site=True,
    )
    Site.clear_site_root_paths_cache()
    return home


@override_settings(CACHES=DATABASE_CACHES)
class TestRenditionCacheQueries(TestCase):
    """Rendition lookups must not read or write the shared database cache."""

    def setUp(self) -> None:
        call_command("createcachetable", verbosity=0)
        self.image_model = get_image_model()

    def test_rendition_cache_backend_is_the_renditions_alias(self) -> None:
        self.assertIs(Rendition.cache_backend, caches["renditions"])

    def _rendition_cache_queries(self, image_count: int, *filters: str) -> int:
        images = [
            self.image_model.objects.create(
                title=f"Cover {image_count}-{index}",
                file=get_test_image_file(),
            )
            for index in range(image_count)
        ]
        cache.clear()
        with CaptureQueriesContext(connection) as queries:
            for image in images:
                image.get_renditions(*filters)
        return django_cache_queries(queries)

    def test_cache_queries_do_not_grow_with_rendition_filters(self) -> None:
        one_width = self._rendition_cache_queries(1, "width-20")
        four_widths = self._rendition_cache_queries(
            1,
            "width-20",
            "width-40",
            "width-60",
            "width-80",
        )

        self.assertEqual(one_width, 0)
        self.assertEqual(four_widths, one_width)

    def test_cache_queries_do_not_grow_with_images(self) -> None:
        one_image = self._rendition_cache_queries(1, "width-20")
        three_images = self._rendition_cache_queries(3, "width-20")

        self.assertEqual(one_image, 0)
        self.assertEqual(three_images, one_image)


@override_settings(CACHES=DATABASE_CACHES)
class TestMagazinePageCacheQueries(TestCase):
    """Magazine pages must read django_cache once, however many links they render."""

    def setUp(self) -> None:
        call_command("createcachetable", verbosity=0)
        self.addCleanup(Site.clear_site_root_paths_cache)
        self.issue = MagazineIssueFactory.create(
            publication_date=timezone.now() - timezone.timedelta(days=1),
        )
        _point_site_at_home()

    def _reads(self, url: str) -> int:
        cache.clear()
        Site.clear_site_root_paths_cache()
        with CaptureQueriesContext(connection) as queries:
            response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        return django_cache_reads(queries)

    def _article_with_links(self, link_count: int) -> MagazineArticle:
        targets = [
            MagazineArticleFactory.create(
                parent=self.issue,
                title=f"Link target {link_count}-{index}",
            )
            for index in range(link_count)
        ]
        html = "".join(
            f'<p><a linktype="page" id="{target.pk}">{target.title}</a></p>'
            for target in targets
        )
        return MagazineArticleFactory.create(
            parent=self.issue,
            is_featured=True,
            title=f"Linked article {link_count}",
            body=[("rich_text", html)],
        )

    def test_article_cache_reads_do_not_grow_with_rich_text_links(self) -> None:
        one_link = self._article_with_links(1)
        one_link_reads = self._reads(one_link.url)
        self.assertContains(self.client.get(one_link.url), "Link target 1-0")

        several_links = self._article_with_links(4)
        several_reads = self._reads(several_links.url)

        self.assertEqual(several_reads, one_link_reads)
        self.assertLessEqual(several_reads, 1)

    def test_issue_page_reads_django_cache_at_most_once(self) -> None:
        cover = get_image_model().objects.create(
            title="Issue cover",
            file=get_test_image_file(),
        )
        self.issue.cover_image = cover
        self.issue.save()

        self.assertLessEqual(self._reads(self.issue.url), 1)

    def test_article_page_reads_django_cache_at_most_once(self) -> None:
        article = self._article_with_links(3)

        self.assertLessEqual(self._reads(article.url), 1)


def _image_table_queries(captured, table: str) -> int:
    return sum(table in query["sql"] for query in captured)


class TestMagazineIndexCoverQueries(TestCase):
    def setUp(self) -> None:
        self.addCleanup(Site.clear_site_root_paths_cache)
        self.index = MagazineIndexPageFactory.create(title="Magazine", slug="magazine")
        _point_site_at_home()
        self.image_model = get_image_model()

    def _cover(self, title: str, *, prepare_renditions: bool = True):
        image = self.image_model.objects.create(
            title=title,
            file=get_test_image_file(filename=f"{title}.gif"),
        )
        if prepare_renditions:
            for spec in ("width-300", "width-500", "width-800", "width-1200"):
                image.get_rendition(spec)
        return image

    def _issue(
        self,
        title: str,
        days_ago: int = 0,
        *,
        publication_date: datetime.date | None = None,
        prepare_renditions: bool = True,
    ) -> MagazineIssue:
        if publication_date is None:
            publication_date = timezone.localdate() - datetime.timedelta(days=days_ago)
        issue = MagazineIssue(
            title=title,
            slug=title.lower().replace(" ", "-"),
            publication_date=publication_date,
            cover_image=self._cover(title, prepare_renditions=prepare_renditions),
        )
        self.index.add_child(instance=issue)
        return issue

    def _image_queries(self, url: str) -> tuple[int, int, HttpResponse]:
        cache.clear()
        Site.clear_site_root_paths_cache()
        with CaptureQueriesContext(connection) as captured:
            response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        return (
            _image_table_queries(captured, "wagtailimages_image"),
            _image_table_queries(captured, "wagtailimages_rendition"),
            response,
        )

    def _assert_cover_urls(
        self,
        response: HttpResponse,
        *issues: MagazineIssue,
    ) -> None:
        for issue in issues:
            for spec in COVER_IMAGE_RENDITION_SPECS:
                rendition = issue.cover_image.get_rendition(spec)
                self.assertContains(response, rendition.url)

    def test_recent_cover_queries_do_not_grow_with_issues(self) -> None:
        recent_one = self._issue("Recent one", 1)
        one_images, one_renditions, one_response = self._image_queries(self.index.url)
        recent_two = self._issue("Recent two", 10)
        recent_three = self._issue("Recent three", 20)
        several_images, several_renditions, several_response = self._image_queries(
            self.index.url,
        )

        self.assertEqual(several_images, one_images)
        self.assertEqual(several_renditions, one_renditions)
        self.assertLessEqual(several_renditions, 1)
        self._assert_cover_urls(one_response, recent_one)
        self._assert_cover_urls(several_response, recent_one, recent_two, recent_three)

    def test_cold_cover_renditions_do_not_query_per_issue(self) -> None:
        cold_one = self._issue("Cold recent one", 1, prepare_renditions=False)
        _one_images, one_renditions, one_response = self._image_queries(self.index.url)
        cold_two = self._issue("Cold recent two", 10, prepare_renditions=False)
        cold_three = self._issue("Cold recent three", 20, prepare_renditions=False)
        _several_images, several_renditions, several_response = self._image_queries(
            self.index.url,
        )

        self.assertEqual(several_renditions, one_renditions)
        self.assertLessEqual(several_renditions, 3)
        self._assert_cover_urls(one_response, cold_one)
        self._assert_cover_urls(several_response, cold_one, cold_two, cold_three)

    def test_archive_year_cover_queries_do_not_grow_with_issues(self) -> None:
        # A fixed month keeps all three issues in one archive year. Offsets of
        # 400, 410, and 420 days can straddle January and the previous December.
        archive_one = self._issue(
            "Archive one",
            publication_date=datetime.date(2019, 6, 1),
        )
        url = f"{self.index.url}?year=2019"
        one_images, one_renditions, one_response = self._image_queries(url)
        archive_two = self._issue(
            "Archive two",
            publication_date=datetime.date(2019, 6, 15),
        )
        archive_three = self._issue(
            "Archive three",
            publication_date=datetime.date(2019, 7, 1),
        )
        several_images, several_renditions, several_response = self._image_queries(url)
        for title in ("Archive one", "Archive two", "Archive three"):
            self.assertContains(several_response, title)
        self._assert_cover_urls(one_response, archive_one)
        self._assert_cover_urls(
            several_response,
            archive_one,
            archive_two,
            archive_three,
        )

        self.assertEqual(several_images, one_images)
        self.assertEqual(several_renditions, one_renditions)
        self.assertLessEqual(several_renditions, 1)
