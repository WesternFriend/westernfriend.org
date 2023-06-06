# import django SimpleTestCase
from django.test import SimpleTestCase

from content_migration.management.import_civicrm_addresses_handler import (
    handle_import_civicrm_addresses,
)


class ImportEventsHandlerSimpleTestCase(SimpleTestCase):
    def test_handle_import_civicrm_addresses(self) -> None:
        assert callable(handle_import_civicrm_addresses)
