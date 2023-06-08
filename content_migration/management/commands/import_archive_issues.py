from django.core.management.base import BaseCommand
from content_migration.management.constants import (
    IMPORT_FILENAMES,
    LOCAL_MIGRATION_DATA_DIRECTORY,
)

from content_migration.management.import_archive_issues_handler import (
    handle_import_archive_issues,
)


class Command(BaseCommand):
    help = "Import Archive Issues from Drupal site"

    def handle(self, *args: tuple, **options: dict[str, str]) -> None:
        file_name = LOCAL_MIGRATION_DATA_DIRECTORY + IMPORT_FILENAMES["archive_issues"]

        handle_import_archive_issues(file_name)
