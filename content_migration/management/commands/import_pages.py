from django.core.management.base import BaseCommand, CommandParser

from content_migration.management.import_pages_handler import handle_import_pages


class Command(BaseCommand):
    help = "Import all Drupal pages"

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("--file", action="store", type=str)

    def handle(self, *args: tuple, **options: dict[str, str]) -> None:
        file_name = options["file"]

        handle_import_pages(file_name)  # type: ignore
