from django.test import TestCase
from community.models import CommunityPage
from memorials.factories import MemorialFactory, MemorialIndexPageFactory
from memorials.models import Memorial, MemorialIndexPage


class MemorialIndexPageFactoryTest(TestCase):
    def test_community_page_creation(self) -> None:
        # Create a community page
        community_page = MemorialIndexPageFactory.create()

        # Now test that it was created
        self.assertIsNotNone(community_page)
        self.assertIsInstance(
            community_page,
            MemorialIndexPage,
        )

        # Test that the MemorialIndexPage instance has a parent
        self.assertIsInstance(
            community_page.get_parent().specific,
            CommunityPage,
        )


class MemorialFactoryTest(TestCase):
    def test_memorial_creation(self) -> None:
        # Create a memorial
        memorial = MemorialFactory.create()

        # Now test that it was created
        self.assertIsNotNone(memorial)
        self.assertIsInstance(
            memorial,
            Memorial,
        )

        # Test that the Memorial instance has a MemorialIndexPage parent
        self.assertIsInstance(
            memorial.get_parent().specific,
            MemorialIndexPage,
        )
