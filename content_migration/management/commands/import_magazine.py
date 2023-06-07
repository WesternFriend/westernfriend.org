from django.core.management.base import BaseCommand
from content_migration.management.constants import LOCAL_MIGRATION_DATA_DIRECTORY

from content_migration.management.import_magazine_handler import handle_import_magazine


class Command(BaseCommand):
    help = "Import all magazine content"

    def handle(self, *args: tuple, **options: dict[str, str]) -> None:
        handle_import_magazine(LOCAL_MIGRATION_DATA_DIRECTORY)  # type: ignore
