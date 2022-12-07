import csv

import pandas as pd
from django.core.management.base import BaseCommand, CommandError
from tqdm import tqdm
from wagtail.core.models import Page

from facets.models import (  # TODO: make sure to add library item topics
    Audience,
    Genre,
    Medium,
    TimePeriod,
    Topic,
)
from library.models import (
    LibraryIndexPage,
    LibraryItem,
    LibraryItemAuthor,
    LibraryItemTopic,
)

from .shared import (
    get_contact_from_author_data,
    get_existing_magazine_author_by_id,
    parse_media_blocks,
)


def add_library_item_authors(
    library_item,
    drupal_author_ids,
    magazine_authors_data: pd.DataFrame,
):
    drupal_author_ids_int = [
        int(author_id) for author_id in drupal_author_ids.split(", ")
    ]

    for drupal_author_id in drupal_author_ids_int:
        author = None

        author_data = get_existing_magazine_author_by_id(
            int(drupal_author_id),
            magazine_authors_data,
        )

        if author_data is not None:
            author = get_contact_from_author_data(author_data)
        else:
            continue

        if author:
            library_item_author_exists = LibraryItemAuthor.objects.filter(
                library_item=library_item,
                author=author,
            ).exists()

            if not library_item_author_exists:
                item_author = LibraryItemAuthor(
                    library_item=library_item,
                    author=author,
                )

                library_item.authors.add(item_author)


def add_library_item_keywords(library_item, keywords):
    for keyword in keywords.split(", "):
        library_item.tags.add(keyword)


class Command(BaseCommand):
    help = "Import all library items"

    def add_arguments(self, parser):
        parser.add_argument(
            "--library_items_file",
            action="store",
            type=str,
        )

        parser.add_argument(
            "--magazine_authors_file",
            action="store",
            type=str,
        )

    def handle(self, *args, **options):
        # Get the only instance of Magazine Department Index Page
        library_item_index_page = LibraryIndexPage.objects.get()

        with open(options["library_items_file"]) as library_items_file:
            library_items_csv = csv.DictReader(library_items_file)
            library_items = list(library_items_csv)

            for import_library_item in tqdm(
                library_items,
                desc="Library items",
                unit="row",
            ):
                library_item_exists = LibraryItem.objects.filter(
                    drupal_node_id=import_library_item["node_id"]
                ).exists()

                if library_item_exists:
                    library_item = LibraryItem.objects.get(
                        drupal_node_id=import_library_item["node_id"]
                    )
                else:
                    library_item = LibraryItem(
                        title=import_library_item["title"],
                        drupal_node_id=import_library_item["node_id"],
                    )

                    # Add library item to library branch of content tree
                    library_item_index_page.add_child(instance=library_item)

                    library_item_index_page.save()

                library_item.title = import_library_item["title"]
                library_item.description = import_library_item["Description"]

                # TODO: Remember to uncomment this line when done developing the remaining import script
                library_item.body = parse_media_blocks(import_library_item["Media"])

                if import_library_item["Audience"] != "":
                    library_item.item_audience = Audience.objects.get(
                        title=import_library_item["Audience"]
                    )

                if import_library_item["Genre"] != "":
                    library_item.item_genre = Genre.objects.get(
                        title=import_library_item["Genre"]
                    )

                if import_library_item["Medium"] != "":
                    library_item.item_medium = Medium.objects.get(
                        title=import_library_item["Medium"]
                    )

                if import_library_item["Time Period"] != "":
                    library_item.item_time_period = TimePeriod.objects.get(
                        title=import_library_item["Time Period"]
                    )

                # Authors
                with open(options["magazine_authors_file"]) as magazine_authors_file:
                    magazine_authors_data = pd.read_csv(magazine_authors_file)
                    # magazine_authors = list(magazine_authors_data)

                    if import_library_item["drupal_magazine_author_ids"] != "":
                        add_library_item_authors(
                            library_item,
                            import_library_item["drupal_magazine_author_ids"],
                            magazine_authors_data,
                        )

                # - Keywords
                if import_library_item["Keywords"] != "":
                    add_library_item_keywords(
                        library_item,
                        import_library_item["Keywords"],
                    )

                # Website
                if import_library_item["Website"] != "":
                    url_stream_block = (
                        "url",
                        import_library_item["Website"],
                    )

                    library_item.body.append(url_stream_block)

                library_item.save()
