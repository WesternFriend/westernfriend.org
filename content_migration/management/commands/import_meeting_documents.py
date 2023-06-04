from django.core.management.base import BaseCommand, CommandParser

from content_migration.management.import_meeting_documents_handler import (
    handle_import_meeting_documents,
)


class Command(BaseCommand):
    help = "Import all meeting documents from CSV file into Wagtail"

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("--file", action="store", type=str)

    def handle(self, *args: tuple, **options: dict[str, str]) -> None:
        file_name = options["file"]
        handle_import_meeting_documents(file_name)  # type: ignore
