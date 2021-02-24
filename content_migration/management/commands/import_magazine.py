from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Import all magazine content"

    def add_arguments(self, parser):
        parser.add_argument("--data_directory", action="store", type=str)

    def handle(self, *args, **options):
        directory = options["data_directory"]

        departments_filename = "departments.csv"
        authors_filename = "authors.csv"
        issues_filename = "issues.csv"
        articles_filename = "articles.csv"

        call_command('import_departments', file=f"{ directory }{ departments_filename }")
        call_command('import_authors', file=f"{ directory }{ authors_filename }")
        call_command('import_issues', file=f"{ directory }{ issues_filename }")
        call_command('import_articles', articles_file=f"{ directory }{ articles_filename }")

