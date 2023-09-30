from tqdm import tqdm
from content_migration.management.shared import parse_csv_file
from facets.models import Topic
from library.helpers import add_library_item_topics
from library.models import LibraryItem, LibraryItemTopic


def handle_import_library_items_topics(file_name) -> None:
    library_items = parse_csv_file(file_name)

    for import_library_item in tqdm(
        library_items,
        desc="Library items",
        unit="row",
    ):
        library_item_exists = LibraryItem.objects.filter(
            drupal_node_id=import_library_item["drupal_node_id"],
        ).exists()


        if library_item_exists:
            library_item = LibraryItem.objects.get(
                drupal_node_id=import_library_item["drupal_node_id"],
            )
        else:
            continue

        add_library_item_topics(
            library_item=library_item,
            topics=import_library_item["topics"],
        )