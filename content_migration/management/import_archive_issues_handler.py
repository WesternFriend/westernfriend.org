from tqdm import tqdm
from content_migration.management.shared import (
    parse_csv_file,
    create_permanent_redirect,
)
from magazine.models import ArchiveIssue, DeepArchiveIndexPage


def create_or_update_archive_issue(
    issue_data: dict,
    deep_archive_index_page: DeepArchiveIndexPage,
) -> ArchiveIssue:
    issue_exists = ArchiveIssue.objects.filter(
        internet_archive_identifier=issue_data["internet_archive_identifier"]
    ).exists()

    if issue_exists:
        # update existing issue
        archive_issue = ArchiveIssue.objects.get(
            internet_archive_identifier=issue_data["internet_archive_identifier"]
        )
        archive_issue.title = issue_data["title"]
        archive_issue.publication_date = issue_data["publication_date"]
        archive_issue.western_friend_volume = issue_data["western_friend_volume"]

        archive_issue.save()
    else:
        archive_issue = ArchiveIssue(
            title=issue_data["title"],
            publication_date=issue_data["publication_date"],
            internet_archive_identifier=issue_data["internet_archive_identifier"],
            western_friend_volume=issue_data["western_friend_volume"],
        )

        # Add issue to site page hiererchy
        deep_archive_index_page.add_child(instance=archive_issue)
        deep_archive_index_page.save()

    return archive_issue


def handle_import_archive_issues(file_name: str) -> None:
    # Get the only instance of Deep Archive Index Page
    deep_archive_index_page = DeepArchiveIndexPage.objects.get()

    issues = parse_csv_file(file_name)

    for issue in tqdm(
        issues,
        desc="Archive issues",
        unit="row",
    ):
        archive_issue = create_or_update_archive_issue(
            issue_data=issue,
            deep_archive_index_page=deep_archive_index_page,
        )

        create_permanent_redirect(
            redirect_path=issue["url_path"],
            redirect_entity=archive_issue,
        )
