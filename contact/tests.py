from django.test import TestCase
from community.models import CommunityPage

from contact.factories import (
    MeetingFactory,
    MeetingIndexPageFactory,
    OrganizationFactory,
    OrganizationIndexPageFactory,
    PersonFactory,
    PersonIndexPageFactory,
)
from contact.models import (
    Meeting,
    MeetingIndexPage,
    Organization,
    OrganizationIndexPage,
    Person,
    PersonIndexPage,
)


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


class MeetingIndexPageFactoryTest(TestCase):
    def test_meeting_index_page_creation(self) -> None:
        # Create a MeetingIndexPage instance
        meeting_index_page = MeetingIndexPageFactory.create()

        # Now test that it was created
        self.assertIsNotNone(meeting_index_page)
        self.assertIsInstance(
            meeting_index_page,
            MeetingIndexPage,
        )

        # Test that the MeetingIndexPage instance has a parent
        self.assertIsInstance(
            meeting_index_page.get_parent().specific,
            CommunityPage,
        )


class MeetingFactoryTest(TestCase):
    def test_meeting_index_page_creation(self) -> None:
        # Create a Meeting instance
        meeting = MeetingFactory.create()

        # Now test that it was created
        self.assertIsNotNone(meeting)
        self.assertIsInstance(
            meeting,
            Meeting,
        )

        # Test that the Meeting instance has a MeetingIndexPage parent
        self.assertIsInstance(
            meeting.get_parent().specific,
            MeetingIndexPage,
        )


class OrganizationIndexPageFactoryTest(TestCase):
    def test_organization_index_page_creation(self) -> None:
        # Create a OrganizationIndexPage instance
        organization_index_page = OrganizationIndexPageFactory.create()

        # Now test that it was created
        self.assertIsNotNone(organization_index_page)
        self.assertIsInstance(
            organization_index_page,
            OrganizationIndexPage,
        )

        # Test that the OrganizationIndexPage instance has a parent
        self.assertIsInstance(
            organization_index_page.get_parent().specific,
            CommunityPage,
        )


class OrganizationFactoryTest(TestCase):
    def test_organization_index_page_creation(self) -> None:
        # Create a Organization instance
        organization = OrganizationFactory.create()

        # Now test that it was created
        self.assertIsNotNone(organization)
        self.assertIsInstance(
            organization,
            Organization,
        )

        # Test that the Organization instance has a OrganizationIndexPage parent
        self.assertIsInstance(
            organization.get_parent().specific,
            OrganizationIndexPage,
        )
