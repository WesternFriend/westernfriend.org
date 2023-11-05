from tqdm import tqdm
from content_migration.management.shared import parse_csv_file
from library.models import LibraryItem


def handle_import_library_items_publication_dates(file_name: str) -> None:
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

        library_item.publication_date = import_library_item["publication_date"]
        library_item.save()
