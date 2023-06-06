# import django SimpleTestCase
from django.test import SimpleTestCase

from content_migration.management.import_civicrm_clerk_relationships_handler import (
    handle_import_civicrm_clerk_relationships,
)


class ImportEventsHandlerSimpleTestCase(SimpleTestCase):
    def test_handle_import_civicrm_clerk_relationships(self) -> None:
        assert callable(handle_import_civicrm_clerk_relationships)
