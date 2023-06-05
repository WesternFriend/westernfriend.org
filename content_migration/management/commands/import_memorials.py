from django.core.management.base import BaseCommand, CommandParser

from content_migration.management.import_memorials_handler import (
    handle_import_memorials,
)


class Command(BaseCommand):
    help = "Import all memorial minutes"

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("--file", action="store", type=str)

    def handle(self, *args: tuple, **options: dict[str, str]) -> None:
        file_name = options["file"]

        handle_import_memorials(file_name)  # type: ignore
