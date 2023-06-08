from django.core.management import call_command

from content_migration.management.constants import IMPORT_FILENAMES


def handle_import_library(directory: str) -> None:
    if not directory.endswith("/"):
        directory += "/"

    library_items_filename = IMPORT_FILENAMES["library_items"]

    call_command(
        "import_library_item_facets",
        folder=f"{ directory }",
    )
    call_command(
        "import_library_items",
        file=f"{ directory }{ library_items_filename }",
    )
