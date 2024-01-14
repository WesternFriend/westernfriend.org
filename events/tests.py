import datetime
from django.http import Http404
from django.test import RequestFactory, TestCase
from django.utils import timezone
from events.factories import EventsIndexPageFactory, EventFactory
from events.models import EventsIndexPage, Event
from home.models import HomePage


class EventsIndexPageFactoryTest(TestCase):
    def test_person_index_page_creation(self) -> None:
        events_index_page = EventsIndexPageFactory.create()

        self.assertIsNotNone(events_index_page)
        self.assertIsInstance(
            events_index_page,
            EventsIndexPage,
        )

        self.assertIsInstance(
            events_index_page.get_parent().specific,
            HomePage,
        )


class EventFactoryTest(TestCase):
    def test_person_creation(self) -> None:
        event = EventFactory.create()

        self.assertIsNotNone(event)
        self.assertIsInstance(
            event,
            Event,
        )

        self.assertIsInstance(
            event.get_parent().specific,
            EventsIndexPage,
        )


class EventsIndexPageTest(TestCase):
    def setUp(self) -> None:
        self.factory = RequestFactory()

        # Create the EventsIndexPage
        self.events_index_page = EventsIndexPageFactory.create()

        base_datetime = timezone.now() + datetime.timedelta(days=10)

        # Create 25 events ordered by date
        self.western_events = [
            EventFactory.create(
                category=Event.EventCategoryChoices.WESTERN,
                start_date=base_datetime + datetime.timedelta(days=i),
            )
            for i in range(13)
        ]
        self.other_events = [
            EventFactory.create(
                category=Event.EventCategoryChoices.OTHER,
                start_date=base_datetime + datetime.timedelta(days=i),
            )
            for i in range(12)
        ]

    def test_get_context_no_category(self) -> None:
        # Create a mock request with no category
        request = self.factory.get("")

        # Call get_context
        context = self.events_index_page.get_context(request)

        # Verify that the context contains the default events
        self.assertEqual(
            list(context["events"].page),
            self.western_events[:10],
        )  # Assumes that EventFactory creates upcoming events
        self.assertEqual(
            context["event_category_title"],
            Event.EventCategoryChoices.WESTERN.capitalize(),
        )

    def test_get_context_valid_category(self) -> None:
        # Create a mock request with a valid category
        request = self.factory.get("?category=other")

        # Call get_context
        context = self.events_index_page.get_context(request)

        # Verify that the context contains the other events
        self.assertEqual(
            list(context["events"].page),
            self.other_events[:10],
        )
        self.assertEqual(
            context["event_category_title"],
            Event.EventCategoryChoices.OTHER.capitalize(),
        )

    def test_get_context_invalid_category(self) -> None:
        # Create a mock request with an invalid category
        request = self.factory.get("?category=invalid")

        # Verify that calling get_context raises a 404
        with self.assertRaises(Http404):
            self.events_index_page.get_context(request)


class TestEventPageGetContext(TestCase):
    def setUp(self) -> None:
        self.factory = RequestFactory()

        # Create an EventsIndexPage instance
        self.events_index_page = EventsIndexPageFactory.create()

        # Create several Event instances
        self.events = []

        total_events = 5
        total_unpublished_events = 3

        # published events
        for i in range(total_events):
            event = EventFactory.create()
            self.events.append(event)

        # unpublished events
        for i in range(total_unpublished_events):
            event = EventFactory.create(live=False)
            self.events.append(event)

    def test_get_context_contains_only_published_events(self) -> None:
        request = self.factory.get("/")
        context = self.events_index_page.get_context(request)

        self.assertIn("events", context)
        # only published events are returned
        self.assertEqual(
            list(context["events"].page.object_list),
            list(Event.objects.live().order_by("start_date")),
        )
