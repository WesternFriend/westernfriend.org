"""Django management command to import news from Drupal."""
from django.core.management import BaseCommand

from content_migration.management.import_news_handler import handle_import_news


class Command(BaseCommand):
    """Django management command to import news from Drupal."""

    help = "Import news from Drupal"

    def handle(self, *args: tuple, **options: dict) -> None:
        """Import news from Drupal."""
        handle_import_news()
