from django.core.management.base import BaseCommand, CommandParser

from content_migration.management.import_archive_articles_handler import (
    handle_import_archive_articles,
)


class Command(BaseCommand):
    help = "Import Archive Articles from Drupal site while linking them to Authors and Issues"  # noqa: E501

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("--file", action="store", type=str)

    def handle(self, *args: tuple, **options: dict[str, str]) -> None:
        handle_import_archive_articles(
            file_name=options["file"],  # type: ignore
        )
