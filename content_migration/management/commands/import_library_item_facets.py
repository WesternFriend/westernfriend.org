from django.core.management.base import BaseCommand
from content_migration.management.constants import LOCAL_MIGRATION_DATA_DIRECTORY

from content_migration.management.import_library_item_facets_handler import (
    handle_import_library_item_facets,
)


class Command(BaseCommand):
    help = "Import all library items"

    def handle(self, *args: tuple, **options: dict[str, str]) -> None:
        handle_import_library_item_facets(
            folder=LOCAL_MIGRATION_DATA_DIRECTORY,
        )
