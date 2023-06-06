# import django SimpleTestCase
from django.test import SimpleTestCase

from content_migration.management.import_civicrm_contacts_handler import (
    handle_import_civicrm_contacts,
)


class ImportEventsHandlerSimpleTestCase(SimpleTestCase):
    def test_handle_import_civicrm_contacts(self) -> None:
        assert callable(handle_import_civicrm_contacts)
