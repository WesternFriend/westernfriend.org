from django.core.management.base import BaseCommand
import numpy as np
import pandas as pd
from tqdm import tqdm
from content_migration.management.commands.shared import parse_body_blocks

from home.models import HomePage
from news.models import NewsIndexPage, NewsItem


class Command(BaseCommand):
    help = "Import all memorial minutes"

    def add_arguments(self, parser):
        parser.add_argument("--file", action="store", type=str)

    def handle(self, *args, **options):
        # Get references to relevant index pages
        home_page = HomePage.objects.get()
        news_index_page = NewsIndexPage.objects.get()

        pages = pd.read_csv(options["file"]).replace({np.nan: None}).to_dict("records")

        for page in tqdm(
            pages,
            total=len(pages),
            desc="Pages",
            unit="row",
        ):
            if page["collection"] == "Extra Extra":
                news_item = NewsItem(
                    title=page["title"],
                    teaser="",
                    drupal_node_id=page["drupal_node_id"],
                    body=parse_body_blocks(page["body"]),
                    body_migrated=page["body"],
                    publication_date=page["publication_date"],
                )

                news_index_page.add_child(instance=news_item)
