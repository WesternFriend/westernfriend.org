from django.test import RequestFactory, TestCase
from community.models import CommunityPage
from contact.factories import MeetingFactory, PersonFactory
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


class MemorialModelTest(TestCase):
    def setUp(self) -> None:
        self.person = PersonFactory(
            given_name="John",
            family_name="Woolman",
        )

    def test_full_name(self) -> None:
        memorial = MemorialFactory(
            memorial_person=self.person,
        )
        self.assertEqual(
            memorial.full_name(),
            "John Woolman",
        )


class MemorialIndexPageModelTest(TestCase):
    def setUp(self) -> None:
        self.factory = RequestFactory()
        self.person: PersonFactory = PersonFactory(
            given_name="John",
            family_name="Woolman",
        )
        self.meeting: MeetingFactory = MeetingFactory(
            title="Test Meeting",
        )

    def test_get_filtered_memorials_title(self) -> None:
        memorial_page: MemorialIndexPage = MemorialIndexPage()
        memorial: Memorial = MemorialFactory(
            title="Test Memorial",
            memorial_person=self.person,
            memorial_meeting=self.meeting,
        )

        request = self.factory.get("/?title=Test Memorial")
        memorials = memorial_page.get_filtered_memorials(request)

        self.assertEqual(memorials.count(), 1)
        self.assertEqual(memorials.first(), memorial)

    def test_get_filtered_memorials_meeting(self) -> None:
        memorial_page: MemorialIndexPage = MemorialIndexPage()
        memorial: MemorialFactory = MemorialFactory(
            title="Test Memorial",
            memorial_person=self.person,
            memorial_meeting=self.meeting,
        )

        request = self.factory.get(f"/?memorial_meeting__title={self.meeting.title}")
        memorials = memorial_page.get_filtered_memorials(request)

        self.assertEqual(memorials.count(), 1)
        self.assertEqual(memorials.first(), memorial)


class MemorialIndexPageGetContextTest(TestCase):
    def setUp(self) -> None:
        self.factory = RequestFactory()
        self.memorial_index_page = MemorialIndexPageFactory.create()
        self.meeting1 = MeetingFactory()
        self.meeting2 = MeetingFactory()
        self.memorial1 = MemorialFactory(memorial_meeting=self.meeting1)
        self.memorial2 = MemorialFactory(memorial_meeting=self.meeting2)

    def test_get_context(self) -> None:
        request = self.factory.get("/")

        context = self.memorial_index_page.get_context(request)

        self.assertIsNotNone(context)
        self.assertIn("memorials", context)
        self.assertIn("meetings", context)

        self.assertEqual(
            len(context["memorials"]),
            2,
        )
        self.assertEqual(
            len(context["meetings"]),
            2,
        )
