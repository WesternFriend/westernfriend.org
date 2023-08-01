from django.test import TestCase


from events.factories import EventIndexPageFactory
from events.models import EventsIndexPage
from home.models import HomePage


class EventsIndexPageFactoryTest(TestCase):
    def test_person_index_page_creation(self) -> None:
        events_index_page = EventIndexPageFactory.create()

        self.assertIsNotNone(events_index_page)
        self.assertIsInstance(
            events_index_page,
            EventsIndexPage,
        )

        self.assertIsInstance(
            events_index_page.get_parent().specific,
            HomePage,
        )
