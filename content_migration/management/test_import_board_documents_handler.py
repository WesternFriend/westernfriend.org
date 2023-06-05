# import django SimpleTestCase
from django.test import SimpleTestCase

from content_migration.management.import_board_documents_handler import (
    handle_import_board_documents,
)


class ImportEventsHandlerSimpleTestCase(SimpleTestCase):
    def test_handle_import_board_documents(self) -> None:
        assert callable(handle_import_board_documents)
