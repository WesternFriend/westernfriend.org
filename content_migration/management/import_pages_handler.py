from tqdm import tqdm
from content_migration.management.shared import parse_body_blocks, parse_csv_file

from home.models import HomePage
from news.models import NewsIndexPage, NewsItem


def handle_import_pages(file_name: str) -> None:
    # Get references to relevant index pages
    HomePage.objects.get()
    news_index_page = NewsIndexPage.objects.get()

    pages = parse_csv_file(file_name)

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
