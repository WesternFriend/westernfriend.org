# import django SimpleTestCase
from django.test import SimpleTestCase

from content_migration.management.import_library_handler import (
    handle_import_library,
)


class ImportEventsHandlerSimpleTestCase(SimpleTestCase):
    def test_handle_import_library(self) -> None:
        assert callable(handle_import_library)
