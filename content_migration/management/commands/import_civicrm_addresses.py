from django.core.management.base import BaseCommand, CommandParser

from content_migration.management.import_civicrm_addresses_handler import (
    handle_import_civicrm_addresses,
)


class Command(BaseCommand):
    help = "Import addresses from CiviCRM"

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("--file", action="store", type=str)

    def handle(self, *args: tuple, **options: dict[str, str]) -> None:
        handle_import_civicrm_addresses(file_name=options["file"])  # type: ignore

        self.stdout.write("All done!")
