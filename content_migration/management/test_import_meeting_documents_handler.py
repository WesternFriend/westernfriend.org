# import django SimpleTestCase
from django.test import SimpleTestCase

from content_migration.management.import_meeting_documents_handler import (
    handle_import_meeting_documents,
)


class ImportEventsHandlerSimpleTestCase(SimpleTestCase):
    def test_handle_import_meeting_documents(self) -> None:
        assert callable(handle_import_meeting_documents)
