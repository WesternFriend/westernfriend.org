import html
from datetime import datetime
from io import BytesIO

import pandas as pd
import requests
from django.core.files.images import ImageFile
from django.core.management.base import BaseCommand, CommandError
from django.utils.timezone import make_aware
from tqdm import tqdm
from wagtail.images.models import Image

from magazine.models import MagazineIndexPage, MagazineIssue


class Command(BaseCommand):
    help = "Import Issues from Drupal site"

    def add_arguments(self, parser):
        parser.add_argument("--file", action="store", type=str)

    def handle(self, *args, **options):
        # Get the only instance of Magazine Index Page
        magazine_index_page = MagazineIndexPage.objects.get()

        issues_list = pd.read_csv(options["file"]).to_dict("records")

        for issue in tqdm(issues_list, desc="Issues", unit="row"):

            issue_exists = MagazineIssue.objects.filter(
                title=issue["title"],
            ).exists()

            # Avoid importing duplicate issues
            # Consider whether we want to update
            # existing issues
            if not issue_exists:
                cover_image_file_name = html.unescape(
                    issue["cover_image_url"].split("/")[-1]
                )
                response = requests.get(issue["cover_image_url"])
                image_file = BytesIO(response.content)

                image = Image(
                    title=issue["title"] + " cover image",
                    file=ImageFile(image_file, name=cover_image_file_name),
                )

                image.save()

                publication_date_tz_aware = make_aware(
                    datetime.strptime(issue["publication_date"], "%Y-%m")
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
