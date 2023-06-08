from django.core.management.base import BaseCommand
from content_migration.management.constants import (
    IMPORT_FILENAMES,
    LOCAL_MIGRATION_DATA_DIRECTORY,
)

from content_migration.management.import_civicrm_clerk_relationships_handler import (  # noqa: E501
    handle_import_civicrm_clerk_relationships,
)


class Command(BaseCommand):
    help = "Import Community Directory from Drupal site"

    def handle(self, *args: tuple, **options: dict[str, str]) -> None:
        file_name = (
            LOCAL_MIGRATION_DATA_DIRECTORY
            + IMPORT_FILENAMES["civicrm_clerk_relationships"]
        )
        handle_import_civicrm_clerk_relationships(file_name)
