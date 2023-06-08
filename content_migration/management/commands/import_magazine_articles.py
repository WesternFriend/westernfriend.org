from django.core.management.base import BaseCommand
from content_migration.management.constants import (
    IMPORT_FILENAMES,
    LOCAL_MIGRATION_DATA_DIRECTORY,
)

from content_migration.management.import_magazine_articles_handler import (
    handle_import_magazine_articles,
)


class Command(BaseCommand):
    help = "Import Articles from Drupal site while linking them to related content"

    def handle(self, *args: tuple, **options: dict[str, str]) -> None:
        file_name = (
            LOCAL_MIGRATION_DATA_DIRECTORY + IMPORT_FILENAMES["magazine_articles"]
        )

        handle_import_magazine_articles(file_name)  # type: ignore
