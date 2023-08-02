import datetime
from django.http import Http404
from django.test import RequestFactory, TestCase
from django.core.paginator import Paginator
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
            list(context["events"]),
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
            list(context["events"]),
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

    def test_get_context_pagination(self) -> None:
        # Test pagination for first page, middle page, last page, and out-of-range page
        for page_number in [1, 2, 3, 4]:
            request = self.factory.get(f"?page={page_number}")
            context = self.events_index_page.get_context(request)

            # Using a Paginator to mimic the pagination logic in get_context
            paginator = Paginator(self.western_events, 10)
            expected_page = paginator.page(min(page_number, paginator.num_pages))

            self.assertEqual(
                list(context["events"]),
                list(expected_page),
            )
