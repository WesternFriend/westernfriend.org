# import django SimpleTestCase
from django.test import SimpleTestCase

from content_migration.management.import_library_item_facets_handler import (
    handle_import_library_item_facets,
)


class ImportEventsHandlerSimpleTestCase(SimpleTestCase):
    def test_handle_import_library_item_facets(self) -> None:
        assert callable(handle_import_library_item_facets)
