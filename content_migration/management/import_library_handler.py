from django.core.management import call_command

from content_migration.management.constants import IMPORT_FILENAMES


def handle_import_library(directory: str) -> None:
    if not directory.endswith("/"):
        directory += "/"

    IMPORT_FILENAMES["library_items"]

    call_command(
        "import_library_item_facets",
    )
    call_command(
        "import_library_items",
    )
