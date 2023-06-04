from django.core.management.base import BaseCommand, CommandParser

from content_migration.management.import_board_documents_handler import (
    handle_import_board_documents,
)


class Command(BaseCommand):
    help = "Import all public board documents from CSV file into Wagtail"

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("--file", action="store", type=str)

    def handle(self, *args: tuple, **options: dict[str, str]) -> None:
        file_name = options["file"]

        handle_import_board_documents(file_name=file_name)  # type: ignore
