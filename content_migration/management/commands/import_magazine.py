from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Import all magazine content"

    def add_arguments(self, parser):
        parser.add_argument("--data-directory", action="store", type=str)

    def handle(self, *args, **options):
        directory = options["data_directory"]

        if not directory.endswith("/"):
            directory += "/"

        magazine_departments_filename = "magazine_departments.csv"
        magazine_authors_filename = "magazine_authors.csv"
        magazine_issues_filename = "magazine_issues.csv"
        magazine_articles_filename = "magazine_articles.csv"

        call_command(
            "import_magazine_departments",
            file=f"{ directory }{ magazine_departments_filename }",
        )
        call_command(
            "import_magazine_authors",
            file=f"{ directory }{ magazine_authors_filename }",
        )
        call_command(
            "import_magazine_issues", file=f"{ directory }{ magazine_issues_filename }"
        )
        call_command(
            "import_magazine_articles",
            articles_file=f"{ directory }{ magazine_articles_filename }",
            authors_file=f"{ directory }{ magazine_authors_filename }",
        )
