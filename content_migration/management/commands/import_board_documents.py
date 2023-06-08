from django.core.management.base import BaseCommand
from content_migration.management.constants import (
    IMPORT_FILENAMES,
    LOCAL_MIGRATION_DATA_DIRECTORY,
)

from content_migration.management.import_board_documents_handler import (
    handle_import_board_documents,
)


class Command(BaseCommand):
    help = "Import all public board documents from CSV file into Wagtail"

    def handle(self, *args: tuple, **options: dict[str, str]) -> None:
        file_name = LOCAL_MIGRATION_DATA_DIRECTORY + IMPORT_FILENAMES["board_documents"]

        handle_import_board_documents(file_name=file_name)
