from django.test import RequestFactory, TestCase
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
from django.urls import reverse
from django.test import Client


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


class TestMeetingGetContext(TestCase):
    def setUp(self) -> None:
        self.request = RequestFactory().get("/")
        self.meeting = MeetingFactory.create()

        self.child_quarterly_meeting = MeetingFactory.build(
            meeting_type=Meeting.MeetingTypeChoices.QUARTERLY_MEETING,
        )
        self.meeting.add_child(instance=self.child_quarterly_meeting)
        self.child_monthly_meeting = MeetingFactory.build(
            meeting_type=Meeting.MeetingTypeChoices.MONTHLY_MEETING,
        )
        self.meeting.add_child(instance=self.child_monthly_meeting)
        self.child_worship_group = MeetingFactory.build(
            meeting_type=Meeting.MeetingTypeChoices.WORSHIP_GROUP,
        )
        self.meeting.add_child(instance=self.child_worship_group)

    def test_meeting_get_context(self) -> None:
        context = self.meeting.get_context(self.request)

        self.assertIn("quarterly_meetings", context)
        self.assertIn("monthly_meetings", context)
        self.assertIn("worship_groups", context)

        self.assertEqual(
            list(context["quarterly_meetings"]),
            [self.child_quarterly_meeting],
        )
        self.assertEqual(
            list(context["monthly_meetings"]),
            [self.child_monthly_meeting],
        )
        self.assertEqual(
            list(context["worship_groups"]),
            [self.child_worship_group],
        )


class TestSlugGeneration(TestCase):
    def test_clean_for_slug(self):
        from contact.static.js.contact.person_url_slug import cleanForSlug

        self.assertEqual(cleanForSlug("carolina-fernández-rodríguez"), "carolina-fernandez-rodriguez")
        self.assertEqual(cleanForSlug("Jürgen Müller"), "jurgen-muller")
        self.assertEqual(cleanForSlug("François Dupont"), "francois-dupont")
        self.assertEqual(cleanForSlug("Miyuki さくら"), "miyuki-sakura")

    def test_generate_autoslug(self):
        client = Client()
        response = client.get(reverse('admin:contact_person_add'))
        self.assertEqual(response.status_code, 200)

        # Simulate filling the form and generating the slug
        form_data = {
            'given_name': 'Carolina',
            'family_name': 'Fernández Rodríguez',
            'slug': '',
        }
        response = client.post(reverse('admin:contact_person_add'), form_data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'carolina-fernandez-rodriguez')
