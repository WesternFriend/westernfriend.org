from content_migration.management.commands.shared import get_contact_from_author_data, get_existing_magazine_author_by_id
import re
from typing import List

from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand, CommandError

from bs4 import BeautifulSoup, Tag as BS4_Tag
import numpy as np
import pandas as pd
from tqdm import tqdm

from wagtail.core.rich_text import RichText


from magazine.models import (
    MagazineArticle,
    MagazineArticleAuthor,
    MagazineDepartment,
    MagazineIssue,
)

from contact.models import Meeting, Organization, Person

from .shared import parse_media_blocks

def extract_pullquotes(item: str) -> List[str]:
    """
    Get a list of all pullquote strings found within the item
    """

    return re.findall(r"\[pullquote\](.+?)\[\/pullquote\]", item.string)


def clean_pullquote_tags(item: BS4_Tag) -> BS4_Tag:
    """
    Replace "[pullquote][/pullquote]" tags in string with "<span class='pullquote'></span>"
    https://stackoverflow.com/a/44593228/1191545
    """

    replacement_values = [
        ("[pullquote]", ""),
        ("[/pullquote]", ""),
    ]

    for replacement_value in replacement_values:
        item.string = item.string.replace(*replacement_value)

    return item


def parse_article_body_blocks(body):
    article_body_blocks = []

    try:
        soup = BeautifulSoup(body, "html.parser")
    except:
        soup = False

        print("Could not parse article body:", body)

    # Placeholder for gathering successive items
    rich_text_value = ""

    if soup:
        for item in soup:

            item_has_value = item.string is not None

            if item_has_value:

                item_contains_pullquote = "pullquote" in item.string

                if item_contains_pullquote:
                    # Add current rich text value as paragraph block, if not empty
                    if rich_text_value != "":
                        rich_text_block = ("paragraph", RichText(rich_text_value))

                        article_body_blocks.append(rich_text_block)

                        # reset rich text value
                        rich_text_value = ""

                    pullquotes = extract_pullquotes(item)

                    # Add Pullquote block(s) to body streamfield
                    # so they appear above the related rich text field
                    # i.e. near the paragraph containing the pullquote
                    for pullquote in pullquotes:
                        block_content = ("pullquote", pullquote)

                        article_body_blocks.append(block_content)

                    item = clean_pullquote_tags(item)

                rich_text_value += str(item)

        if rich_text_value != "":
            # Add Paragraph Block with remaining rich text elements
            rich_text_block = ("paragraph", RichText(rich_text_value))

            article_body_blocks.append(rich_text_block)

    return article_body_blocks


def parse_article_authors(article, article_authors, magazine_authors):

    for drupal_author_id in article_authors.split(", "):
        drupal_author_id = int(drupal_author_id)

        author_data = get_existing_magazine_author_by_id(drupal_author_id, magazine_authors)

        author = get_contact_from_author_data(author_data)

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
        related_issue = MagazineIssue.objects.get(
            title=issue_title
        )
    except ObjectDoesNotExist:
        print("Can't find issue: ", issue_title)

    related_issue.add_child(instance=article)


class Command(BaseCommand):
    help = "Import Articles from Drupal site while linking them to Authors, Issues, Deparments, and Keywords"

    def add_arguments(self, parser):
        parser.add_argument("--articles_file", action="store", type=str)
        parser.add_argument("--authors_file", action="store", type=str)

    def handle(self, *args, **options):
        articles = pd.read_csv(options["articles_file"], dtype={"Authors": str})
        magazine_authors = pd.read_csv(options["authors_file"])

        for index, row in tqdm(
            articles.iterrows(), total=articles.shape[0], desc="Articles", unit="row"
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
                article_body_blocks = parse_article_body_blocks(row["Body"])
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
                article = parse_article_authors(article, row["Authors"], magazine_authors)

            # Assign keywards to article
            if row["Keywords"] is not np.nan:
                for keyword in row["Keywords"].split(", "):
                    article.tags.add(keyword)

            article.save()
