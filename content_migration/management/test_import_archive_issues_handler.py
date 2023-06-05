# import django SimpleTestCase
from django.test import SimpleTestCase

from content_migration.management.import_archive_issues_handler import (
    handle_import_archive_issues,
)


class ImportEventsHandlerSimpleTestCase(SimpleTestCase):
    def test_handle_import_archive_issues(self) -> None:
        assert callable(handle_import_archive_issues)
