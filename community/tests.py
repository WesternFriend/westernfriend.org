from django.test import TestCase

from community.models import CommunityPage
from contact.models import PersonIndexPage
from home.models import HomePage
from .factories import CommunityPageFactory, PersonIndexPageFactory


class CommunityPageFactoryTest(TestCase):
    def test_community_page_creation(self) -> None:
        # Create a community page
        community_page = CommunityPageFactory.create()

        # Now test that it was created
        self.assertIsNotNone(community_page)
        self.assertIsInstance(community_page, CommunityPage)

        # Test that the CommunityPage instance has a parent
        self.assertIsInstance(community_page.get_parent().specific, HomePage)


class PersonIndexPageFactoryTest(TestCase):
    def test_person_index_page_creation(self) -> None:
        # Create a PersonIndexPage instance
        person_index_page = PersonIndexPageFactory.create()

        # Now test that it was created
        self.assertIsNotNone(person_index_page)
        self.assertIsInstance(person_index_page, PersonIndexPage)

        # Test that the PersonIndexPage instance has a parent
        self.assertIsInstance(person_index_page.get_parent().specific, CommunityPage)
