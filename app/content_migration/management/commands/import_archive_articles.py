import numpy as np
import pandas as pd
from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand
from tqdm import tqdm

from wagtail.models import Page
from content_migration.management.commands.shared import (
    get_existing_magazine_author_from_db,
)

from magazine.models import ArchiveArticle, ArchiveArticleAuthor, ArchiveIssue


def create_archive_article_authors(archive_article, authors):
    """Create an ArchiveArticleAuthor instance for each author, if any"""

    if authors is not np.nan:
        # Create table of contents
        # assigning articles to each ToC item

        # Get each author ID as an integer
        authors_list = map(int, authors.split(", "))

        if authors_list is not None:
            for drupal_author_id in authors_list:
                contact = get_existing_magazine_author_from_db(
                    drupal_author_id,
                )

                if contact is not None:
                    article_author = ArchiveArticleAuthor(
                        article=archive_article,
                        author=contact,
                    )

                    article_author.save()


class Command(BaseCommand):
    help = "Import Archive Articles from Drupal site while linking them to Authors and Issues"

    def add_arguments(self, parser):
        parser.add_argument("--file", action="store", type=str)
        # parser.add_argument("--authors_file", action="store", type=str)

    def handle(self, *args, **options):
        articles = pd.read_csv(
            options["file"],
            dtype={"authors": str},
        )

        grouped_articles = articles.groupby("internet_archive_identifier")
        # for issue in tqdm(issues, desc="Archive issues", unit="row"):
        for internet_archive_identifier, issue_articles in tqdm(
            grouped_articles, desc="Archive articles", unit="row"
        ):
            try:
                issue = ArchiveIssue.objects.get(
                    internet_archive_identifier=internet_archive_identifier
                )
            except ObjectDoesNotExist:
                print(
                    "Could not find archive issue with identifier:",
                    internet_archive_identifier,
                )

            for index, article_data in issue_articles.iterrows():

                # Create archive article instance with initial fields
                pdf_page_number = None

                if not np.isnan(article_data["pdf_page_number"]):
                    pdf_page_number = article_data["pdf_page_number"]

                toc_page_number = None

                if not np.isnan(article_data["toc_page_number"]):
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

                create_archive_article_authors(archive_article, article_data["authors"])
