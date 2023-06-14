"""Django management command to import all archive issues and articles."""
from django.core.management.base import BaseCommand
from django.core.management import call_command


class Command(BaseCommand):
    """Import all archive issues and articles."""

    help = "Import all archive issues and articles"

    def handle(self, *args: tuple, **options: dict) -> None:
        """Handle the command."""
        call_command("import_archive_issues")
        call_command("import_archive_articles")
