from django.core.management.base import BaseCommand
from content_migration.management.constants import LOCAL_MIGRATION_DATA_DIRECTORY

from content_migration.management.import_library_handler import handle_import_library


class Command(BaseCommand):
    help = "Import all Library content"

    def handle(self, *args: tuple, **options: dict[str, str]) -> None:
        directory = LOCAL_MIGRATION_DATA_DIRECTORY

        handle_import_library(directory)  # type: ignore
