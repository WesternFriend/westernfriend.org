import csv

from django.core.management.base import BaseCommand, CommandError
from tqdm import tqdm

from magazine.models import DeepArchiveIndexPage, ArchiveIssue


class Command(BaseCommand):
    help = "Import Archive Issues from Drupal site"

    def add_arguments(self, parser):
        parser.add_argument("--file", action="store", type=str)

    def handle(self, *args, **options):
        # Get the only instance of Deep Archive Index Page
        deep_archive_index_page = DeepArchiveIndexPage.objects.get()

        with open(options["file"]) as import_file:
            issues = csv.DictReader(import_file)

            for issue in tqdm(
                issues, desc="Archive issues", unit="row"
            ):
                if not ArchiveIssue.objects.filter(internet_archive_identifier=issue["internet_archive_identifier"]).exists():
                    import_issue = ArchiveIssue(
                        title=issue["title"],
                        publication_date=issue["publication_date"],
                        internet_archive_identifier=issue["internet_archive_identifier"],
                        western_friend_volume=issue["western_friend_volume"],
                    )

                    # Add issue to site page hiererchy
                    deep_archive_index_page.add_child(instance=import_issue)
                    deep_archive_index_page.save()

        self.stdout.write("All done!")
