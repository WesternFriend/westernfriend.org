from django.test import TestCase

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
