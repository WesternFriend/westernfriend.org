from django.test import RequestFactory, TestCase

from community.models import CommunityPage, OnlineWorship, OnlineWorshipIndexPage
from home.models import HomePage
from .factories import (
    CommunityPageFactory,
    OnlineWorshipIndexPageFactory,
    OnlineWorshipFactory,
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

        for i in range(total_online_worship_pages):
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
