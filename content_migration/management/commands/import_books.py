from django.core.management.base import BaseCommand
from content_migration.management.constants import (
    IMPORT_FILENAMES,
    LOCAL_MIGRATION_DATA_DIRECTORY,
)

from content_migration.management.import_books_handler import (
    handle_import_books,
)


class Command(BaseCommand):
    help = "Import all bookstore books from CSV file into Wagtail"

    def handle(self, *args: tuple, **options: dict[str, str]) -> None:
        file_name = LOCAL_MIGRATION_DATA_DIRECTORY + IMPORT_FILENAMES["books"]

        handle_import_books(file_name=file_name)
