from django.core.management.base import BaseCommand
from content_migration.management.constants import (
    IMPORT_FILENAMES,
    LOCAL_MIGRATION_DATA_DIRECTORY,
)

from content_migration.management.import_pages_handler import handle_import_pages


class Command(BaseCommand):
    help = "Import all Drupal pages"

    def handle(self, *args: tuple, **options: dict[str, str]) -> None:
        file_name = LOCAL_MIGRATION_DATA_DIRECTORY + IMPORT_FILENAMES["pages"]

        handle_import_pages(file_name)  # type: ignore
