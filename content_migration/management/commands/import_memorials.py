from django.core.management.base import BaseCommand
from content_migration.management.constants import (
    IMPORT_FILENAMES,
    LOCAL_MIGRATION_DATA_DIRECTORY,
)

from content_migration.management.import_memorials_handler import (
    handle_import_memorials,
)


class Command(BaseCommand):
    help = "Import all memorial minutes"

    def handle(self, *args: tuple, **options: dict[str, str]) -> None:
        file_name = LOCAL_MIGRATION_DATA_DIRECTORY + IMPORT_FILENAMES["memorials"]

        handle_import_memorials(file_name)  # type: ignore
