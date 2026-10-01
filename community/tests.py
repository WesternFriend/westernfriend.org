from datetime import time

from django.test import RequestFactory, TestCase

from community.models import (
    CommunityDirectoryIndexPage,
    CommunityPage,
    OnlineWorship,
    OnlineWorshipIndexPage,
)
from home.models import HomePage

from .factories import (
    CommunityDirectoryFactory,
    CommunityPageFactory,
    OnlineWorshipFactory,
    OnlineWorshipIndexPageFactory,
)


class CommunityPageFactoryTest(TestCase):
    def test_community_page_creation(self) -> None:
        # Create a community page
        community_page = CommunityPageFactory.create()

        # Now test that it was created
        self.assertIsNotNone(community_page)
        self.assertIsInstance(community_page, CommunityPage)

        # Test that the CommunityPage instance has a parent
        self.assertIsInstance(
            community_page.get_parent().specific,
            HomePage,
        )


class OnlineWorshipIndexPageFactoryTest(TestCase):
    def test_online_worship_index_page_creation(self) -> None:
        # Create an OnlineWorshipIndexPage instance
        online_worship_index_page = OnlineWorshipIndexPageFactory.create()

        # Now test that it was created
        self.assertIsNotNone(online_worship_index_page)
        self.assertIsInstance(
            online_worship_index_page,
            OnlineWorshipIndexPage,
        )

        # Test that the OnlineWorshipIndexPage instance has a parent
        self.assertIsInstance(
            online_worship_index_page.get_parent().specific,
            CommunityPage,
        )


class OnlineWorshipFactoryTest(TestCase):
    def test_online_worship_creation(self) -> None:
        # Create an OnlineWorship instance
        online_worship = OnlineWorshipFactory.create()

        # Now test that it was created
        self.assertIsNotNone(online_worship)
        self.assertIsInstance(
            online_worship,
            OnlineWorship,
        )

        # Test that the OnlineWorship instance has a OnlineWorshipIndexPage parent
        self.assertIsInstance(
            online_worship.get_parent().specific,
            OnlineWorshipIndexPage,
        )


class TestOnlineWorshipIndexPageGetContext(TestCase):
    def setUp(self) -> None:
        self.factory = RequestFactory()

        # Create an OnlineWorshipIndexPage instance
        self.online_worship_index_page = OnlineWorshipIndexPageFactory.create()

        # Create several OnlineWorship instances
        self.online_worship_pages = []

        total_online_worship_pages = 5

        for _i in range(total_online_worship_pages):
            online_worship_page = OnlineWorshipFactory.create()
            self.online_worship_pages.append(online_worship_page)

    def test_get_context(self) -> None:
        # Create an instance of a GET request.
        request = self.factory.get("/")
        context = self.online_worship_index_page.get_context(request)

        self.assertIn("online_worship_meetings", context)
        self.assertEqual(
            list(context["online_worship_meetings"]),
            list(OnlineWorship.objects.live().order_by("title")),
        )


class CommunityDirectoryFactoryTest(TestCase):
    def test_creates_directory_under_its_index_page(self) -> None:
        directory = CommunityDirectoryFactory.create()

        index_page = directory.get_parent().specific
        self.assertIsInstance(index_page, CommunityDirectoryIndexPage)
        self.assertIsInstance(index_page.get_parent().specific, CommunityPage)
        self.assertTrue(directory.website)

        second = CommunityDirectoryFactory.create()
        self.assertEqual(second.get_parent(), directory.get_parent())


class TimesOfWorshipFormattingTest(TestCase):
    """The 12-hour clock in the factory has to work on every platform."""

    @staticmethod
    def _times_of_worship(hour: int, minute: int = 0) -> str:
        return OnlineWorshipFactory.build(
            online_worship_time=time(hour, minute),
            online_worship_day="Sunday",
            online_worship_timezone="America/Los_Angeles",
        ).times_of_worship

    def test_morning_hour_has_no_leading_zero(self) -> None:
        self.assertIn("9:30 AM", self._times_of_worship(9, 30))

    def test_afternoon_hour_uses_the_12_hour_clock(self) -> None:
        self.assertIn("1:05 PM", self._times_of_worship(13, 5))

    def test_noon_is_twelve_pm(self) -> None:
        self.assertIn("12:00 PM", self._times_of_worship(12))

    def test_midnight_is_twelve_am(self) -> None:
        # hour % 12 is 0 here, which is exactly where a naive version breaks.
        self.assertIn("12:00 AM", self._times_of_worship(0))
