import csv
from datetime import datetime
import requests
from io import BytesIO

from tqdm import tqdm

from django.core.files.images import ImageFile
from django.core.management.base import BaseCommand, CommandError
from django.utils.timezone import make_aware

from wagtail.images.models import Image

from magazine.models import MagazineIndexPage, MagazineIssue


class Command(BaseCommand):
    help = "Import Issues from Drupal site"

    def add_arguments(self, parser):
        parser.add_argument("--file", action="store", type=str)

    def handle(self, *args, **options):
        # Get the only instance of Magazine Index Page
        magazine_index_page = MagazineIndexPage.objects.get()

        with open(options["file"]) as import_file:
            issues = csv.DictReader(import_file)
            issues_list = list(issues)

            for issue in tqdm(issues_list, desc="Issues", unit="row"):
                response = requests.get(issue["cover_image_url"])
                image_file = BytesIO(response.content)

                image = Image(
                    title=issue["title"] + " cover image",
                    file=ImageFile(image_file, name=issue["cover_image_file_name"]),
                )

                image.save()

                publication_date_tz_aware = make_aware(
                    datetime.strptime(
                        issue["publication_date"],
                        "%Y-%m-%d"
                    )
                )

                import_issue = MagazineIssue(
                    title=issue["title"],
                    publication_date=publication_date_tz_aware,
                    first_published_at=publication_date_tz_aware,
                    issue_number=issue["issue_number"],
                    cover_image=image,
                )

                # Add issue to site page hiererchy
                magazine_index_page.add_child(instance=import_issue)
                magazine_index_page.save()

        self.stdout.write("All done!")
