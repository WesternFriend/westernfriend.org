from django.core.management.base import BaseCommand, CommandParser


class Command(BaseCommand):
    help = "Import all memorial minutes"

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("--file", action="store", type=str)

    def handle(self, *args: tuple, **options: dict[str, str]) -> None:
        options["file"]
