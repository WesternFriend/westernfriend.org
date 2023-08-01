from django.test import TestCase
from community.models import CommunityPage

from contact.factories import PersonFactory, PersonIndexPageFactory
from contact.models import Person, PersonIndexPage


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


class PersonFactoryTest(TestCase):
    def test_person_index_page_creation(self) -> None:
        # Create a Person instance
        person = PersonFactory.create()

        # Now test that it was created
        self.assertIsNotNone(person)
        self.assertIsInstance(
            person,
            Person,
        )

        # Test that the Person instance has a PersonIndexPage parent
        self.assertIsInstance(
            person.get_parent().specific,
            PersonIndexPage,
        )
