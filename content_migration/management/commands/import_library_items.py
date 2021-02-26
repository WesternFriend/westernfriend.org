import csv

from django.core.management.base import BaseCommand, CommandError

from tqdm import tqdm

from library.models import LibraryIndexPage, LibraryItem


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

            for library_item_dict in tqdm(
                library_items, desc="Library items", unit="row"
            ):
                library_item_exists = LibraryItem.objects.filter(
                    drupal_node_id=library_item_dict["node_id"]
                ).exists()

                if library_item_exists:
                    library_item = LibraryItem.objects.get(
                        drupal_node_id=library_item_dict["node_id"]
                    )
                else:
                    library_item = LibraryItem(title=library_item_dict["title"])

                # Add library item to library
                library_item_index_page.add_child(instance=library_item)
                library_item_index_page.save()
