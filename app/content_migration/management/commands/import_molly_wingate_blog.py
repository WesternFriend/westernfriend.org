from django.core.management.base import BaseCommand
from django.db import IntegrityError
import numpy as np
import pandas as pd
from tqdm import tqdm
from content_migration.management.commands.shared import (
    parse_body_blocks,
)
from wagtail.contrib.redirects.models import Redirect

from wf_pages.models import MollyWingateBlogIndexPage, MollyWingateBlogPage


class Command(BaseCommand):
    help = "Import all Molly Wingate Blog content"

    def add_arguments(self, parser):
        parser.add_argument("--file", action="store", type=str)

    def handle(self, *args, **options):
        blog_items_data = (
            pd.read_csv(options["file"]).replace({np.nan: None}).to_dict("records")
        )

        # Get a reference to the MollyWingateBlogIndexPage object
        molly_wingate_blog_index_page = MollyWingateBlogIndexPage.objects.get()

        for blog_item in tqdm(
            blog_items_data,
            total=len(blog_items_data),
            desc="Blog Items",
            unit="row",
        ):
            # Check if blog item already exists
            blog_item_exists = MollyWingateBlogPage.objects.filter(
                drupal_node_id=blog_item["drupal_node_id"]
            ).exists()

            if blog_item_exists:
                continue

            molly_wingate_blog_page = MollyWingateBlogPage(
                title=blog_item["title"],
                publication_date=blog_item["publication_date"],
                drupal_node_id=blog_item["drupal_node_id"],
                body=parse_body_blocks(blog_item["body"]),
                body_migrated=blog_item["body"],
            )

            if blog_item["topic"] is not None:
                molly_wingate_blog_page.tags.add(
                    blog_item["topic"],
                )

            # Add the blog page to the blog index
            molly_wingate_blog_index_page.add_child(instance=molly_wingate_blog_page)

            try:
                Redirect.objects.create(
                    old_path=blog_item["url_path"],
                    redirect_page=molly_wingate_blog_page,
                    site=molly_wingate_blog_page.get_site(),
                )
            except IntegrityError:
                pass
