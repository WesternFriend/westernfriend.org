from django.core.management.base import BaseCommand
from content_migration.management.constants import (
    IMPORT_FILENAMES,
    LOCAL_MIGRATION_DATA_DIRECTORY,
)

from content_migration.management.handlers.import_events_handler import (
    handle_import_events,
)


class Command(BaseCommand):
    help = "Import Events from Drupal site"

    def handle(self, *args: tuple, **options: dict) -> None:
        file_name = LOCAL_MIGRATION_DATA_DIRECTORY + IMPORT_FILENAMES["events"]
        handle_import_events(file_name=file_name)
