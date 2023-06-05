import numpy as np
import pandas as pd
from tqdm import tqdm  # type: ignore
from content_migration.management.shared import parse_body_blocks

from home.models import HomePage
from news.models import NewsIndexPage, NewsItem


def handle_import_pages(file_name: str) -> None:
    # Get references to relevant index pages
    HomePage.objects.get()
    news_index_page = NewsIndexPage.objects.get()

    pages = pd.read_csv(file_name).replace({np.nan: None}).to_dict("records")

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
