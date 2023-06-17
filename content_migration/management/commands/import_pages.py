from django.core.management.base import BaseCommand

from content_migration.management.import_pages_handler import handle_import_pages
from content_migration.management.shared import construct_import_file_path


class Command(BaseCommand):
    help = "Import all Drupal pages"

    def handle(self, *args: tuple, **options: dict[str, str]) -> None:
        file_name = construct_import_file_path("pages")

        handle_import_pages(file_name)  # type: ignore
