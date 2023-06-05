# import django SimpleTestCase
from django.test import SimpleTestCase

from content_migration.management.import_magazine_departments_handler import (  # noqa: E501
    handle_import_magazine_departments,
)


class ImportEventsHandlerSimpleTestCase(SimpleTestCase):
    def test_handle_import_magazine_departments(self) -> None:
        assert callable(handle_import_magazine_departments)
