from tqdm import tqdm

from content_migration.management.shared import (
    create_permanent_redirect,
    parse_csv_file,
    parse_media_blocks,
    parse_media_string_to_list,
)

from content_migration.management.shared import (
    construct_import_file_path,
    parse_body_blocks,
)

from news.models import NewsIndexPage, NewsItem


def handle_import_news_item(
    news_item: dict,
    news_index_page: NewsIndexPage,
) -> NewsItem:
    """Import a single news item from Drupal."""

    # check if news item exists
    news_item_exists = NewsItem.objects.filter(
        drupal_node_id=news_item["drupal_node_id"],
    ).exists()

    if news_item_exists:
        news_item_db = NewsItem.objects.get(drupal_node_id=news_item["drupal_node_id"])
        news_item_db.title = news_item["title"]
        news_item_db.publication_date = news_item["publication_date"]
        news_item_db.body = parse_body_blocks(news_item["body"])
        if news_item["media"] != "":
            news_item_db.body += parse_media_blocks(
                parse_media_string_to_list(news_item["media"]),
            )
        news_item_db.body_migrated = news_item["body"]

        news_item_db.save()
    else:
        news_item_db = NewsItem(
            title=news_item["title"],
            publication_date=news_item["publication_date"],
            body=parse_body_blocks(news_item["body"]),
            body_migrated=news_item["body"],
            drupal_node_id=news_item["drupal_node_id"],
        )
        if news_item["media"] != "":
            news_item_db.body += parse_media_blocks(
                parse_media_string_to_list(news_item["media"]),
            )

        news_index_page.add_child(instance=news_item_db)

    return news_item_db


def handle_import_news() -> None:
    """Import news from Drupal."""
    news_items_data = parse_csv_file(
        construct_import_file_path(file_key="extra_extra"),
    )
    news_index_page = NewsIndexPage.objects.get()

    for news_item_data in tqdm(
        news_items_data,
        desc="News items",
    ):
        news_item_db: NewsItem = handle_import_news_item(
            news_item=news_item_data,
            news_index_page=news_index_page,
        )

        create_permanent_redirect(
            redirect_path=news_item_data["url_path"],
            redirect_entity=news_item_db,
        )
