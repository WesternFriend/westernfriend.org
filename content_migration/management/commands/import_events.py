from django.core.management.base import BaseCommand, CommandParser

from content_migration.management.handlers.import_events_handler import (
    handle_import_events,
)


class Command(BaseCommand):
    help = "Import Events from Drupal site"

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("--file", action="store", type=str)

    def handle(self, *args: tuple, **options: dict) -> None:
        handle_import_events(file_name=options["file"])
        self.stdout.write("All done!")
