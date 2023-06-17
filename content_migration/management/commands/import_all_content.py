"""Django management command to run all content importers."""
from django.core.management import BaseCommand, call_command


class Command(BaseCommand):
    """Django management command to run all content importers."""

    help = "Import all content from Drupal"

    def handle(self, *args: tuple, **options: dict) -> None:
        """Run all content importers."""
        call_command("import_magazine")
        call_command("import_library")
        call_command("import_archive")
        call_command("import_memorials")
        call_command("import_events")
        call_command("import_board_documents")
        call_command("import_meeting_documents")
        call_command("import_molly_wingate_blog")
        call_command("import_news")
        call_command("import_online_worship")
        # TODO: add remaining importers
        # - pages
        # - CiviCRM
        #   - contacts,
        #   - addresses,
        #   - clerk relationships,
        #   - meeting relationships
