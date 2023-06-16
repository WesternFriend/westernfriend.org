"""Management command to import Online Worship content."""
from django.core.management.base import BaseCommand

from content_migration.management.import_online_worship_handler import (
    handle_import_online_worship,
)


class Command(BaseCommand):
    """Import Online Worship content."""

    help = "Import Online Worship content"

    def handle(self, *args: tuple, **options: dict) -> None:
        """Import Online Worship content."""
        handle_import_online_worship()
