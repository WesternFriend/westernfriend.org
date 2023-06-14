"""Django management command to run all content importers."""
from django.core.management import BaseCommand, call_command


class Command(BaseCommand):
    """Django management command to run all content importers."""

    help = "Import all content from Drupal"

    def handle(self, *args: tuple, **options: dict) -> None:
        """Run all content importers."""
        call_command("import_magazine", interactive=False)
        call_command("import_library", interactive=False)
        call_command("import_archive", interactive=False)
        call_command("import_memorials", interactive=False)
        call_command("import_events", interactive=False)
        call_command("import_board_documents", interactive=False)
        call_command("import_molly_wingate_blog", interactive=False)
        # TODO: add remaining importers
        # - news
        # - pages
        # - meeting documents
        # - CiviCRM
        #   - contacts,
        #   - addresses,
        #   - clerk relationships,
        #   - meeting relationships
