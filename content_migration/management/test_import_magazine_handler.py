# import django SimpleTestCase
from django.test import SimpleTestCase

from content_migration.management.import_magazine_handler import (
    handle_import_magazine,
)


class ImportEventsHandlerSimpleTestCase(SimpleTestCase):
    def test_handle_import_magazine(self) -> None:
        assert callable(handle_import_magazine)
