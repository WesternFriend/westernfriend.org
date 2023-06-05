from django.core.management.base import BaseCommand, CommandParser

from content_migration.management.import_magazine_handler import handle_import_magazine


class Command(BaseCommand):
    help = "Import all magazine content"

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("--data-directory", action="store", type=str)

    def handle(self, *args: tuple, **options: dict[str, str]) -> None:
        directory = options["data_directory"]

        handle_import_magazine(directory)  # type: ignore
