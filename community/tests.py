from django.test import TestCase

from community.models import CommunityPage
from home.models import HomePage
from .factories import CommunityPageFactory


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
