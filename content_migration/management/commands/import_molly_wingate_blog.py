"""Django management command that calls the
import_molly_wingate_blog_handler.py."""
from django.core.management.base import BaseCommand
from content_migration.management.import_molly_wingate_blog_handler import (
    handle_import_molly_wingate_blog,
)


class Command(BaseCommand):
    """Django management command that calls the
    import_molly_wingate_blog_handler.py."""

    help = "Import Molly Wingate's blog"

    def handle(self, *args: tuple, **options: dict[str, str]) -> None:
        """Django management command that calls the
        import_molly_wingate_blog_handler.py."""
        handle_import_molly_wingate_blog()  # type: ignore
