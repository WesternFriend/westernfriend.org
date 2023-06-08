import logging

from django.core.exceptions import ObjectDoesNotExist
from tqdm import tqdm
from content_migration.management.errors import (
    CouldNotFindMatchingContactError,
    DuplicateContactError,
)

from magazine.models import (
    MagazineArticle,
    MagazineArticleAuthor,
    MagazineDepartment,
    MagazineIssue,
)

from content_migration.management.shared import (
    get_existing_magazine_author_from_db,
    parse_csv_file,
    parse_media_blocks,
    parse_body_blocks,
)

logging.basicConfig(
    filename="import_log_magazine_articles.log",
    level=logging.ERROR,
    format="%(message)s",
    # format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)


def parse_article_authors(
    article: MagazineArticle,
    article_authors: str,
) -> MagazineArticle:
    """Fetch all related article authors and create an article relationship."""
    for drupal_author_id in article_authors.split(", "):
        try:
            author = get_existing_magazine_author_from_db(
                drupal_author_id,
            )
        except (
            CouldNotFindMatchingContactError,
            DuplicateContactError,
        ):
            logger.error(
                f"Could not find author from Drupal ID: { drupal_author_id }",
            )
            continue

        article_author = MagazineArticleAuthor(
            article=article,
            author=author,
        )

        article.authors.add(article_author)

    return article


def assign_article_to_issue(
    article: MagazineArticle,
    drupal_issue_node_id: int,
) -> None:
    try:
        related_issue = MagazineIssue.objects.get(
            drupal_node_id=drupal_issue_node_id,
        )
    except ObjectDoesNotExist:
        print("Can't find issue: ", drupal_issue_node_id)

    related_issue.add_child(
        instance=article,
    )


def handle_import_magazine_articles(file_name: str) -> None:
    articles_data = parse_csv_file(file_name)

    for row in tqdm(
        articles_data,
        desc="Articles",
        unit="row",
    ):
        article_exists = MagazineArticle.objects.filter(
            drupal_node_id=row["node_id"]
        ).exists()

        # Skip import for existing articles
        if article_exists:
            continue

        department = MagazineDepartment.objects.get(
            title=row["department"],
        )

        article_body_blocks = []
        body_migrated = None

        if row["body"] != "":
            article_body_blocks = parse_body_blocks(row["body"])
            body_migrated = row["body"]

        # Download and parse article media
        if row["media"] != "":
            media_blocks = parse_media_blocks(row["media"].split(", "))

            # Merge media blocks with article body blocks
            article_body_blocks += media_blocks

        article = MagazineArticle(
            title=row["title"],
            body=article_body_blocks,
            body_migrated=body_migrated,
            department=department,
            drupal_node_id=row["node_id"],
        )

        # Assign article to issue
        assign_article_to_issue(
            article=article,
            drupal_issue_node_id=row["related_issue_id"],
        )

        # Assign authors to article
        if row["authors"] != "":
            article = parse_article_authors(
                article,
                row["authors"],
            )

        # Assign keywards to article
        if row["keywords"] != "":
            for keyword in row["keywords"].split(", "):
                article.tags.add(keyword)

        article.save()
