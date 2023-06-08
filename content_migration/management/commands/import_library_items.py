from django.core.management.base import BaseCommand
from content_migration.management.constants import (
    IMPORT_FILENAMES,
    LOCAL_MIGRATION_DATA_DIRECTORY,
)

from content_migration.management.import_library_items_handler import (
    handle_import_library_items,
)


class Command(BaseCommand):
    help = "Import all library items"

    def handle(self, *args: tuple, **options: dict[str, str]) -> None:
        file_name = LOCAL_MIGRATION_DATA_DIRECTORY + IMPORT_FILENAMES["library_items"]

        handle_import_library_items(file_name=file_name)  # type: ignore
