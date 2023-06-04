from django.core.management import call_command


def handle_import_library(directory: str) -> None:
    if not directory.endswith("/"):
        directory += "/"

    library_items_filename = "library_items.csv"

    call_command(
        "import_library_item_facets",
        folder=f"{ directory }",
    )
    call_command(
        "import_library_items",
        file=f"{ directory }{ library_items_filename }",
    )
