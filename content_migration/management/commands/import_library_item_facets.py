from django.core.management.base import BaseCommand, CommandParser

from content_migration.management.import_library_item_facets_handler import (
    handle_import_library_item_facets,
)


class Command(BaseCommand):
    help = "Import all library items"

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("--folder", action="store", type=str)

    def handle(self, *args: tuple, **options: dict[str, str]) -> None:
        handle_import_library_item_facets(folder=options["folder"])  # type: ignore
