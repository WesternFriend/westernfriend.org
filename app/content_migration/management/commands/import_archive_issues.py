import csv

import pandas as pd
from django.core.management.base import BaseCommand, CommandError
from tqdm import tqdm

from magazine.models import ArchiveIssue, DeepArchiveIndexPage


class Command(BaseCommand):
    help = "Import Archive Issues from Drupal site"

    def add_arguments(self, parser):
        parser.add_argument("--file", action="store", type=str)

    def handle(self, *args, **options):
        # Get the only instance of Deep Archive Index Page
        deep_archive_index_page = DeepArchiveIndexPage.objects.get()

        issues = pd.read_csv(options["file"]).to_dict("records")

        for issue in tqdm(issues, desc="Archive issues", unit="row"):
            issue_exists = ArchiveIssue.objects.filter(
                internet_archive_identifier=issue["internet_archive_identifier"]
            ).exists()

            if not issue_exists:
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
