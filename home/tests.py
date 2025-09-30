from django.utils import timezone
from django.test import RequestFactory, TestCase
from wagtail.models import Page

from home.models import HomePage
from events.factories import EventFactory
from events.models import Event
from magazine.factories import MagazineIssueFactory
from magazine.models import MagazineIssue

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
