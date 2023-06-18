from django.core.management.base import BaseCommand

from content_migration.management.import_civicrm_contacts_handler import (
    handle_import_civicrm_contacts,
)
from content_migration.management.shared import construct_import_file_path


class Command(BaseCommand):
    help = "Import Contacts Directory from Drupal site"

    def handle(self, *args: tuple, **options: dict[str, str]) -> None:
        handle_import_civicrm_contacts(
            file_name=construct_import_file_path("civicrm_contacts")
        )
