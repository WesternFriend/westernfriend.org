import math

from django.core.management.base import BaseCommand, CommandError

import numpy as np
import pandas as pd

from wagtail.core.models import Page
from wagtail.core.blocks import ListBlock, PageChooserBlock

from contact.models import Meeting, Organization, Person
from magazine.models import ArchiveIssue
from magazine.blocks import ArchiveArticleBlock


class Command(BaseCommand):
    help = "Import Archive Articles from Drupal site while linking them to Authors and Issues"

    def add_arguments(self, parser):
        parser.add_argument("--articles_file", action="store", type=str)
        # parser.add_argument("--authors_file", action="store", type=str)

    def handle(self, *args, **options):
        articles = pd.read_csv(options["articles_file"])

        authors = pd.read_csv("../import_data/authors_cleaned_deduped-2020-04-12.csv")

        grouped_articles = articles.groupby("internet_archive_identifier")

        missing_archive_issues = 0

        for internet_archive_identifier, issue_articles in grouped_articles:
            table_of_contents_blocks = []

            for index, article in issue_articles.iterrows():
                article_authors = []

                if article["authors"] is not np.nan:
                    # Create table of contents
                    # assigning articles to each ToC item

                    # split the comma separated list of authors
                    # ensuring it is a string
                    authors_list = str(article["authors"]).split(", ")

                    if authors_list != None:

                        for author in authors_list:
                            authors_mask = authors["drupal_full_name"] == author
                            author_data = authors[authors_mask].iloc[0].to_dict()

                            if author_data["organization_name"] is not np.nan:
                                author = Organization.objects.get(
                                    drupal_full_name=author_data["drupal_full_name"]
                                )
                            elif author_data["meeting_name"] is not np.nan:
                                author = Meeting.objects.get(
                                    drupal_full_name=author_data["drupal_full_name"]
                                )
                            else:
                                author = Person.objects.get(
                                    drupal_full_name=author_data["drupal_full_name"]
                                )

                            article_authors.append(author)

                archive_article_block = {
                    "title": article["title"],
                    "authors": article_authors,
                }

                if not math.isnan(article["toc_page_number"]):
                    archive_article_block["toc_page_number"] = int(
                        article["toc_page_number"]
                    )

                if not math.isnan(article["pdf_page_number"]):
                    archive_article_block["pdf_page_number"] = int(
                        article["pdf_page_number"]
                    )

                current_article = ("Article", archive_article_block)

                table_of_contents_blocks.append(current_article)

            try:
                related_issue = ArchiveIssue.objects.get(
                    internet_archive_identifier=internet_archive_identifier
                )

                related_issue.table_of_contents = table_of_contents_blocks

                related_issue.save()
            except:
                missing_archive_issues += 1

        print("Total missing issues: ", missing_archive_issues)
