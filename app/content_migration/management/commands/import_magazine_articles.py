import numpy as np
import pandas as pd

from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand
from tqdm import tqdm

from content_migration.management.commands.shared import (
    get_contact_from_author_data,
    get_existing_magazine_author_by_id,
)
from magazine.models import (
    MagazineArticle,
    MagazineArticleAuthor,
    MagazineDepartment,
    MagazineIssue,
)

from .shared import parse_media_blocks, parse_body_blocks


def parse_article_authors(article, article_authors, magazine_authors_data):

    for drupal_author_id in article_authors.split(", "):
        drupal_author_id = int(drupal_author_id)

        author_data = get_existing_magazine_author_by_id(
            drupal_author_id,
            magazine_authors_data,
        )

        if author_data is not None:
            author = get_contact_from_author_data(author_data)
        else:
            print("Could not find author data for Drupal author ID:", drupal_author_id)
            continue

        if author is not None:
            article_author = MagazineArticleAuthor(
                article=article,
                author=author,
            )

            article.authors.add(article_author)
        else:
            print("Could not find author from Drupal ID:", drupal_author_id)

    return article


def assign_article_to_issue(article, issue_title):
    try:
        related_issue = MagazineIssue.objects.get(title=issue_title)
    except ObjectDoesNotExist:
        print("Can't find issue: ", issue_title)

    related_issue.add_child(instance=article)


class Command(BaseCommand):
    help = "Import Articles from Drupal site while linking them to Authors, Issues, Deparments, and Keywords"  # noqa: E501

    def add_arguments(self, parser):
        parser.add_argument(
            "--articles_file",
            action="store",
            type=str,
        )
        parser.add_argument(
            "--authors_file",
            action="store",
            type=str,
        )

    def handle(self, *args, **options):
        articles_data = pd.read_csv(options["articles_file"], dtype={"Authors": str})
        magazine_authors_data = pd.read_csv(options["authors_file"])

        for _index, row in tqdm(
            articles_data.iterrows(),
            total=articles_data.shape[0],
            desc="Articles",
            unit="row",
        ):
            article_exists = MagazineArticle.objects.filter(
                drupal_node_id=row["node_id"]
            ).exists()

            # Skip import for existing articles
            if article_exists:
                continue

            department = MagazineDepartment.objects.get(title=row["Department"])

            article_body_blocks = []
            body_migrated = None

            if row["Body"] is not np.nan:
                article_body_blocks = parse_body_blocks(row["Body"])
                body_migrated = row["Body"]

            # Download and parse article media
            if row["Media"] is not np.nan:
                media_blocks = parse_media_blocks(row["Media"])

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
            assign_article_to_issue(article, row["related_issue_title"])

            # Assign authors to article
            if row["Authors"] is not np.nan:
                article = parse_article_authors(
                    article,
                    row["Authors"],
                    magazine_authors_data,
                )

            # Assign keywards to article
            if row["Keywords"] is not np.nan:
                for keyword in row["Keywords"].split(", "):
                    article.tags.add(keyword)

            article.save()
