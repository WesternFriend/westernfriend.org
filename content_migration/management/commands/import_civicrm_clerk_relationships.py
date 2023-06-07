from django.core.management.base import BaseCommand, CommandParser

from content_migration.management.import_civicrm_clerk_relationships_handler import (  # noqa: E501
    handle_import_civicrm_clerk_relationships,
)


class Command(BaseCommand):
    help = "Import Community Directory from Drupal site"

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("--file", action="store", type=str)

    def handle(self, *args: tuple, **options: dict[str, str]) -> None:
        file_name = options["file"]
        handle_import_civicrm_clerk_relationships(file_name)  # type: ignore

        self.stdout.write("All done!")
