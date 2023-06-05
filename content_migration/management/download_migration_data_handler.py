import os
import urllib.request

from content_migration.management.constants import (
    LOCAL_MIGRATION_DATA_DIRECTORY,
)

FILENAMES = [
    "magazine_issues.csv",
    "magazine_articles.csv",
    "archive_issues.csv",
    "archive_articles.csv",
    "library_items.csv",
    "pages.csv",
    "memorials.csv",
    "events.csv",
    "magazine_authors.csv",
    "magazine_departments.csv",
    "library_item_audience.csv",
    "library_item_genre.csv",
    "library_item_medium.csv",
    "library_item_time_period.csv",
    "library_item_topic.csv",
]


def handle_file_downloads(data_directory_url: str) -> None:
    # ensure url ends with a slash
    if not data_directory_url.endswith("/"):
        data_directory_url += "/"

    # ensure local directory exists
    if not os.path.exists(LOCAL_MIGRATION_DATA_DIRECTORY):
        os.makedirs(LOCAL_MIGRATION_DATA_DIRECTORY)

    # download files
    for filename in FILENAMES:
        download_url = f"{data_directory_url}{filename}"
        local_file_path = f"{LOCAL_MIGRATION_DATA_DIRECTORY}{filename}"

        urllib.request.urlretrieve(
            url=download_url,
            filename=local_file_path,
        )
