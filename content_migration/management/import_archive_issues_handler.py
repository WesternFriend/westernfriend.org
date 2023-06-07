from tqdm import tqdm
from content_migration.management.shared import parse_csv_file

from magazine.models import ArchiveIssue, DeepArchiveIndexPage


def handle_import_archive_issues(file_name: str) -> None:
    # Get the only instance of Deep Archive Index Page
    deep_archive_index_page = DeepArchiveIndexPage.objects.get()

    issues = parse_csv_file(file_name)

    for issue in tqdm(
        issues,
        desc="Archive issues",
        unit="row",
    ):
        issue_exists = ArchiveIssue.objects.filter(
            internet_archive_identifier=issue["internet_archive_identifier"]
        ).exists()

        if issue_exists:
            continue

        import_issue = ArchiveIssue(
            title=issue["title"],
            publication_date=issue["publication_date"],
            internet_archive_identifier=issue["internet_archive_identifier"],
            western_friend_volume=issue["western_friend_volume"],
        )

        # Add issue to site page hiererchy
        deep_archive_index_page.add_child(instance=import_issue)
        deep_archive_index_page.save()
