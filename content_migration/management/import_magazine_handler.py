from django.core.management import call_command

from content_migration.management.constants import IMPORT_FILENAMES


def handle_import_magazine(directory: str) -> None:
    if not directory.endswith("/"):
        directory += "/"

        call_command(
            "import_magazine_departments",
            file=f"{ directory }{ IMPORT_FILENAMES['magazine_departments'] }",
        )
        call_command(
            "import_magazine_authors",
            file=f"{ directory }{ IMPORT_FILENAMES['magazine_authors'] }",
        )
        call_command(
            "import_magazine_issues",
            file=f"{ directory }{ IMPORT_FILENAMES['magazine_issues'] }",
        )
        call_command(
            "import_magazine_articles",
            articles_file=f"{ directory }{ IMPORT_FILENAMES['magazine_articles'] }",
            authors_file=f"{ directory }{ IMPORT_FILENAMES['magazine_authors'] }",
        )
