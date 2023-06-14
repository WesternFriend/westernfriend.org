import logging

from django.core.exceptions import ObjectDoesNotExist
from tqdm import tqdm
from content_migration.management.errors import (
    CouldNotFindMatchingContactError,
    DuplicateContactError,
)

from content_migration.management.shared import (
    create_archive_issues_from_articles_dicts,
    get_existing_magazine_author_from_db,
    parse_csv_file,
)
from magazine.models import ArchiveArticle, ArchiveArticleAuthor, ArchiveIssue

logging.basicConfig(
    filename="import_archive_articles.log",
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)


def create_archive_article_authors(
    archive_article: ArchiveArticle,
    authors: str,
) -> None:
    """Create an ArchiveArticleAuthor instance for each author, if any."""

    if authors != "":
        # Create table of contents
        # assigning articles to each ToC item

        # Get each author ID as an integer
        authors_list = list(map(int, authors.split(", ")))

        if len(authors_list) == 0:
            # Create an ArchiveArticleAuthor instance for each author
            return

        for drupal_author_id in authors_list:
            try:
                contact = get_existing_magazine_author_from_db(
                    drupal_author_id,
                )
            except (
                CouldNotFindMatchingContactError,
                DuplicateContactError,
            ):
                continue

            article_author_exists = ArchiveArticleAuthor.objects.filter(
                article=archive_article,
                author=contact,
            ).exists()

            if not article_author_exists:
                article_author = ArchiveArticleAuthor(
                    article=archive_article,
                    author=contact,
                )

                article_author.save()


def handle_import_archive_articles(file_name: str) -> None:
    articles = parse_csv_file(file_name)

    archive_issues = create_archive_issues_from_articles_dicts(
        articles=articles,
    )

    # for issue in tqdm(issues, desc="Archive issues", unit="row"):
    for archive_issue in tqdm(
        archive_issues,
        desc="Archive articles",
        unit="row",
    ):
        try:
            issue = ArchiveIssue.objects.get(
                internet_archive_identifier=archive_issue.internet_archive_identifier
            )
        except ObjectDoesNotExist:
            error_message = f"Could not find archive issue with identifier: { archive_issue.internet_archive_identifier }"  # noqa: E501
            logger.error(error_message)

        for article_data in archive_issue.archive_articles:
            # Create archive article instance with initial fields
            pdf_page_number = None

            if article_data["pdf_page_number"] != "":
                pdf_page_number = article_data["pdf_page_number"]

            toc_page_number = None

            if article_data["toc_page_number"] != "":
                toc_page_number = article_data["toc_page_number"]

            article_exists = ArchiveArticle.objects.filter(
                drupal_node_id=article_data["drupal_node_id"]
            ).exists()

            if article_exists:
                archive_article = ArchiveArticle.objects.get(
                    drupal_node_id=article_data["drupal_node_id"]
                )
                # Make sure all fields are updated
                archive_article.title = article_data["title"]
                archive_article.issue = issue
                archive_article.toc_page_number = toc_page_number
                archive_article.pdf_page_number = pdf_page_number
                archive_article.drupal_node_id = article_data["drupal_node_id"]
            else:
                # Create a new archive article
                archive_article = ArchiveArticle(
                    title=article_data["title"],
                    issue=issue,
                    toc_page_number=toc_page_number,
                    pdf_page_number=pdf_page_number,
                    drupal_node_id=article_data["drupal_node_id"],
                )

            archive_article.save()

            # Create an ArchiveArticleAuthor instance for each author
            if article_data["authors"] != "":
                create_archive_article_authors(
                    archive_article,
                    article_data["authors"],
                )
