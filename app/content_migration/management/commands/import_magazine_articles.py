import logging

import numpy as np
import pandas as pd

from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand
from tqdm import tqdm

from magazine.models import (
    MagazineArticle,
    MagazineArticleAuthor,
    MagazineDepartment,
    MagazineIssue,
)

from .shared import (
    get_existing_magazine_author_from_db,
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


def parse_article_authors(article, article_authors):
    """
    Fetch all related article authors and create an article relationship.
    """
    for drupal_author_id in article_authors.split(", "):
        drupal_author_id = int(drupal_author_id)
        author = get_existing_magazine_author_from_db(drupal_author_id)

        if author is not None:
            article_author = MagazineArticleAuthor(
                article=article,
                author=author,
            )

            article.authors.add(article_author)
        else:
            print("Could not find author from Drupal ID:", drupal_author_id)

    return article


def assign_article_to_issue(article, drupal_issue_node_id):
    try:
        related_issue = MagazineIssue.objects.get(
            drupal_node_id=drupal_issue_node_id,
        )
    except ObjectDoesNotExist:
        print("Can't find issue: ", drupal_issue_node_id)

    related_issue.add_child(
        instance=article,
    )


class Command(BaseCommand):
    help = "Import Articles from Drupal site while linking them to related content"

    def add_arguments(self, parser):
        parser.add_argument(
            "--file",
            action="store",
            type=str,
        )

    def handle(self, *args, **options):
        articles_data = (
            pd.read_csv(options["file"]).replace({np.nan: None}).to_dict("records")
        )

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

            if row["body"] is not None:
                article_body_blocks = parse_body_blocks(row["body"])
                body_migrated = row["body"]

            # Download and parse article media
            if row["media"] is not None:
                media_blocks = parse_media_blocks(row["media"])

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
            if row["authors"] is not None:
                article = parse_article_authors(
                    article,
                    row["authors"],
                )

            # Assign keywards to article
            if row["keywords"] is not None:
                for keyword in row["keywords"].split(", "):
                    article.tags.add(keyword)

            article.save()
