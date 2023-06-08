from django.core.management.base import BaseCommand, CommandParser
from content_migration.management.constants import (
    IMPORT_FILENAMES,
    LOCAL_MIGRATION_DATA_DIRECTORY,
)

from content_migration.management.import_civicrm_addresses_handler import (
    handle_import_civicrm_addresses,
)


class Command(BaseCommand):
    help = "Import addresses from CiviCRM"

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("--file", action="store", type=str)

    def handle(self, *args: tuple, **options: dict[str, str]) -> None:
        file_name = (
            LOCAL_MIGRATION_DATA_DIRECTORY + IMPORT_FILENAMES["civicrm_addresses"]
        )
        handle_import_civicrm_addresses(file_name=file_name)  # type: ignore
