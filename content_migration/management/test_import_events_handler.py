# import django SimpleTestCase
from django.test import SimpleTestCase

from content_migration.management.import_events_handler import (
    handle_import_events,
)


class ImportEventsHandlerSimpleTestCase(SimpleTestCase):
    def test_handle_import_events(self) -> None:
        assert callable(handle_import_events)
