# import django SimpleTestCase
from django.test import SimpleTestCase

from content_migration.management.import_library_items_handler import (
    handle_import_library_items,
)


class ImportEventsHandlerSimpleTestCase(SimpleTestCase):
    def test_handle_import_library_items(self) -> None:
        assert callable(handle_import_library_items)
