# import django SimpleTestCase
from django.test import SimpleTestCase

from content_migration.management.import_pages_handler import (
    handle_import_pages,
)


class ImportEventsHandlerSimpleTestCase(SimpleTestCase):
    def test_handle_import_pages(self) -> None:
        assert callable(handle_import_pages)
