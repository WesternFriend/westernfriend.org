from django.core.management.base import BaseCommand
from content_migration.management.constants import (
    IMPORT_FILENAMES,
    LOCAL_MIGRATION_DATA_DIRECTORY,
)
from content_migration.management.import_library_items_topics_handler import (
    handle_import_library_items_topics,
)


class Command(BaseCommand):
    help = "Description of your command"

    def handle(self, *args, **options):
        file_name = LOCAL_MIGRATION_DATA_DIRECTORY + IMPORT_FILENAMES["library_items"]

        handle_import_library_items_topics(file_name=file_name)
