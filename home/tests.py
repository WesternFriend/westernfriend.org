from urllib.parse import urljoin

from django.templatetags.static import static
from django.utils import timezone
from django.test import RequestFactory, TestCase
from wagtail.models import Page, Site

from home.models import HomePage
from contact.factories import PersonFactory
from events.factories import EventFactory
from events.models import Event
from magazine.factories import MagazineArticleFactory, MagazineIssueFactory
from magazine.models import MagazineArticleAuthor, MagazineIssue

from .factories import HomePageFactory


class HomePageFactoryTest(TestCase):
    def test_home_page_creation(self) -> None:
        home_page = HomePageFactory.create()

        # Now test that it was created
        self.assertIsNotNone(home_page)
        self.assertIsInstance(
            home_page,
            HomePage,
        )

        # Verify the home page is a direct child of the root page
        self.assertEqual(
            home_page.get_parent(),
            Page.get_first_root_node(),
        )


class TestHomePage(TestCase):
    def setUp(self) -> None:
        self.factory = RequestFactory()
        self.home_page = HomePageFactory.create()

    def test_get_context(self) -> None:
        MagazineIssueFactory.create_batch(5)
        EventFactory.create_batch(
            5,
            is_featured=True,
            start_date=timezone.now() + timezone.timedelta(days=1),
        )

        request = self.factory.get("/")
        context = self.home_page.get_context(request)

        self.assertIn("current_issue", context)
        self.assertIn("featured_events", context)

        self.assertEqual(
            context["current_issue"],
            MagazineIssue.objects.live().order_by("-publication_date").first(),
        )
        expected_featured_events = (
            Event.objects.live()
            .filter(
                start_date__gte=timezone.now(),
                is_featured=True,
            )
            .order_by("start_date")[:3]
        )
        self.assertQuerySetEqual(
            context["featured_events"],
            expected_featured_events,
        )


class HomePageRenderTest(TestCase):
    def setUp(self) -> None:
        self.home_page = HomePageFactory.create()
        Site.objects.all().delete()
        Site.objects.create(
            hostname="testserver",
            root_page=self.home_page,
            is_default_site=True,
        )
        Site.clear_site_root_paths_cache()
        self.addCleanup(Site.clear_site_root_paths_cache)

    def test_renders_current_issue_and_featured_content(self) -> None:
        issue = MagazineIssueFactory.create(
            publication_date=timezone.now() - timezone.timedelta(days=1),
        )
        article = MagazineArticleFactory.create(parent=issue, is_featured=True)
        author = PersonFactory.create()
        former_author = PersonFactory.create()
        former_author.unpublish()
        for person in (author, former_author):
            MagazineArticleAuthor.objects.create(article=article, author=person)
        event = EventFactory.create(is_featured=True)

        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Current Issue")
        self.assertContains(response, article.title)
        self.assertContains(response, f'href="{author.url}"')
        self.assertContains(response, former_author.title)
        self.assertContains(response, event.title)
        self.assertContains(response, event.url)

    def test_head_and_structured_data_use_absolute_urls(self) -> None:
        response = self.client.get("/")

        self.assertContains(
            response,
            '<link rel="canonical" href="http://testserver/" />',
        )
        self.assertContains(response, '"@id": "http://testserver/#organization"')
        og_image = urljoin("http://testserver/", static("img/og-default.jpg"))
        self.assertContains(
            response,
            f'<meta property="og:image" content="{og_image}" />',
        )
        self.assertNotContains(response, "http:///")

    def test_social_description_uses_search_description(self) -> None:
        self.home_page.search_description = "Quaker writing from the West"
        self.home_page.save_revision().publish()

        response = self.client.get("/")

        self.assertContains(
            response,
            '<meta property="og:description" content="Quaker writing from the West" />',
        )
        self.assertNotContains(response, "{{")
