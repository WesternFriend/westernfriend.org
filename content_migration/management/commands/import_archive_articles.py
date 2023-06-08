from django.core.management.base import BaseCommand
from content_migration.management.constants import (
    IMPORT_FILENAMES,
    LOCAL_MIGRATION_DATA_DIRECTORY,
)

from content_migration.management.import_archive_articles_handler import (
    handle_import_archive_articles,
)


class Command(BaseCommand):
    help = "Import Archive Articles from Drupal site while linking them to Authors and Issues"  # noqa: E501

    def handle(self, *args: tuple, **options: dict[str, str]) -> None:
        file_name = (
            LOCAL_MIGRATION_DATA_DIRECTORY + IMPORT_FILENAMES["archive_articles"]
        )

        handle_import_archive_articles(
            file_name=file_name,
        )
