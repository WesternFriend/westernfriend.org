from django.core.management.base import BaseCommand
from content_migration.management.constants import (
    IMPORT_FILENAMES,
    LOCAL_MIGRATION_DATA_DIRECTORY,
)

from content_migration.management.import_meeting_documents_handler import (
    handle_import_meeting_documents,
)


class Command(BaseCommand):
    help = "Import all meeting documents from CSV file into Wagtail"

    def handle(self, *args: tuple, **options: dict[str, str]) -> None:
        file_name = (
            LOCAL_MIGRATION_DATA_DIRECTORY + IMPORT_FILENAMES["meeting_documents"]
        )
        handle_import_meeting_documents(file_name)  # type: ignore
