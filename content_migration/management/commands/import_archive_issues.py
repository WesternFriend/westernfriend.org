from django.core.management.base import BaseCommand, CommandParser


class Command(BaseCommand):
    help = "Import Archive Issues from Drupal site"

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("--file", action="store", type=str)

    def handle(self, *args: tuple, **options: dict[str, str]) -> None:
        options["file"]

        self.stdout.write("All done!")
