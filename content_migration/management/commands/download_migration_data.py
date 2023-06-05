from django.core.management.base import BaseCommand, CommandParser

from content_migration.management.download_migration_data_handler import (
    handle_file_downloads,
)


class Command(BaseCommand):
    help = "Download migration data"

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "data_directory_url",
            type=str,
            help="Data directory URL",
        )

    def handle(self, *args: tuple, **options: dict[str, str]) -> None:
        data_directory_url: str = options["data_directory_url"]  # type: ignore

        handle_file_downloads(data_directory_url)
