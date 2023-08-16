import html
from datetime import datetime
from io import BytesIO

import requests
from django.core.files.images import ImageFile
from django.utils.timezone import make_aware
from tqdm import tqdm
from wagtail.images.models import Image
from content_migration.management.shared import (
    create_permanent_redirect,
    parse_csv_file,
)

from magazine.models import MagazineIndexPage, MagazineIssue


def handle_import_magazine_issues(file_name: str) -> None:
    # Get the only instance of Magazine Index Page
    magazine_index_page = MagazineIndexPage.objects.get()

    issues_list = parse_csv_file(file_name)

    for issue in tqdm(issues_list, desc="Issues", unit="row"):
        issue_exists = MagazineIssue.objects.filter(
            title=issue["title"],
        ).exists()

        # Avoid importing duplicate issues
        # Consider whether we want to update
        # existing issues
        if not issue_exists:
            cover_image_file_name = html.unescape(
                issue["cover_image_url"].split("/")[-1],
            )
            response = requests.get(issue["cover_image_url"])
            image_file = BytesIO(response.content)

            image = Image(
                title=issue["title"] + " cover image",
                file=ImageFile(image_file, name=cover_image_file_name),
            )

            image.save()

            publication_date_tz_aware = make_aware(
                datetime.strptime(issue["publication_date"], "%Y-%m-%d"),
            )

            import_issue = MagazineIssue(
                title=issue["title"],
                publication_date=publication_date_tz_aware,
                first_published_at=publication_date_tz_aware,
                issue_number=issue["issue_number"],
                cover_image=image,
                drupal_node_id=issue["drupal_node_id"],
            )

            # Add issue to site page hiererchy
            magazine_index_page.add_child(instance=import_issue)
            magazine_index_page.save()

            create_permanent_redirect(
                redirect_path=issue["url_path"],
                redirect_entity=import_issue,
            )
