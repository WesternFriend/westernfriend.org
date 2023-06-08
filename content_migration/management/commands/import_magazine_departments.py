from django.core.management.base import BaseCommand
from content_migration.management.constants import (
    IMPORT_FILENAMES,
    LOCAL_MIGRATION_DATA_DIRECTORY,
)

from content_migration.management.import_magazine_departments_handler import (
    handle_import_magazine_departments,
)


class Command(BaseCommand):
    help = "Import Departments from Drupal site"

    def handle(self, *args: tuple, **options: dict[str, str]) -> None:
        file_name = (
            LOCAL_MIGRATION_DATA_DIRECTORY + IMPORT_FILENAMES["magazine_departments"]
        )

        handle_import_magazine_departments(file_name)  # type: ignore
