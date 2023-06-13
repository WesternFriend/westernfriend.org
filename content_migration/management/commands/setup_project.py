"""Define a management command that runs the setup_development_project
function."""
from django.core.management.base import BaseCommand

from content_migration.management.setup_project_handler import (
    setup_project,
)


class Command(BaseCommand):
    help = "Setup a development project"

    def handle(self, *args: tuple, **options: dict[str, str]) -> None:
        """Run the setup_development_project function."""
        setup_project()
