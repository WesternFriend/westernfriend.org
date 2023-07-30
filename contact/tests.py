from django.test import TestCase
from community.models import CommunityPage

from contact.factories import PersonIndexPageFactory
from contact.models import PersonIndexPage


class PersonIndexPageFactoryTest(TestCase):
    def test_person_index_page_creation(self) -> None:
        # Create a PersonIndexPage instance
        person_index_page = PersonIndexPageFactory.create()

        # Now test that it was created
        self.assertIsNotNone(person_index_page)
        self.assertIsInstance(
            person_index_page,
            PersonIndexPage,
        )

        # Test that the PersonIndexPage instance has a parent
        self.assertIsInstance(
            person_index_page.get_parent().specific,
            CommunityPage,
        )
