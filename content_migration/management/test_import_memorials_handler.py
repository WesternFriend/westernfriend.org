# import django SimpleTestCase
from django.test import SimpleTestCase

from content_migration.management.import_memorials_handler import (
    handle_import_memorials,
)


class ImportEventsHandlerSimpleTestCase(SimpleTestCase):
    def test_handle_import_memorials(self) -> None:
        assert callable(handle_import_memorials)
