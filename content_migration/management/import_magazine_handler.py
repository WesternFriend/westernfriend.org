from django.core.management import call_command


def handle_import_magazine(directory: str) -> None:
    if not directory.endswith("/"):
        directory += "/"

    call_command(
        "import_magazine_departments",
    )
    call_command(
        "import_magazine_authors",
    )
    call_command(
        "import_magazine_issues",
    )
    call_command(
        "import_magazine_articles",
    )
