from django.core.management.base import BaseCommand, CommandParser

from content_migration.management.import_magazine_departments_handler import (
    handle_import_magazine_departments,
)


class Command(BaseCommand):
    help = "Import Departments from Drupal site"

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("--file", action="store", type=str)

    def handle(self, *args: tuple, **options: dict[str, str]) -> None:
        file_name = options["file"]

        handle_import_magazine_departments(file_name)  # type: ignore
