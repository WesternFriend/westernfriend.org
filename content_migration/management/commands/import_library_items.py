import csv

from django.core.management.base import BaseCommand, CommandError

from tqdm import tqdm

from facets.models import (
    Audience,
    Genre,
    Medium,
    TimePeriod,
    Topic,
)
from library.models import LibraryIndexPage, LibraryItem, LibraryItemTopic

from .shared import parse_media_blocks


class Command(BaseCommand):
    help = "Import all library items"

    def add_arguments(self, parser):
        parser.add_argument("--file", action="store", type=str)

    def handle(self, *args, **options):
        # Get the only instance of Magazine Department Index Page
        library_item_index_page = LibraryIndexPage.objects.get()

        with open(options["file"]) as import_file:
            library_items_csv = csv.DictReader(import_file)
            library_items = list(library_items_csv)

            for import_library_item in tqdm(
                library_items, desc="Library items", unit="row"
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

                library_item.title = import_library_item["title"]
                library_item.description = import_library_item["Description"]
                library_item.item_audience = Audience.objects.get(
                    title=import_library_item["Audience"]
                )
                library_item.item_genre = Genre.objects.get(
                    title=import_library_item["Genre"]
                )
                library_item.item_medium = Medium.objects.get(
                    title=import_library_item["Medium"]
                )
                library_item.item_time_period = TimePeriod.objects.get(
                    title=import_library_item["Time Period"]
                )

                if not library_item_exists:
                    # Add library item to library
                    library_item_index_page.add_child(instance=library_item)
                    library_item_index_page.save()

                library_item.save()
