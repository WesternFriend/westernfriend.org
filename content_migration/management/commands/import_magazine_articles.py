import re
from typing import List

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


def get_existing_magazine_author_by_id(drupal_author_id, magazine_authors):
    """
    Get an author and check if it is duplicate. Return existing author
    """
    authors_mask = magazine_authors["drupal_author_id"] == drupal_author_id

    if authors_mask.sum() == 0:
        print("Author not found:", drupal_author_id)
    if authors_mask.sum() > 1:
        print("Duplicate authors found:", drupal_author_id)

    try:
        author_data = magazine_authors[authors_mask].iloc[0].to_dict()
    except IndexError:
        print("Index error")

    # Get existing author, if this author is a duplicate
    if not np.isnan(author_data["duplicate of ID"]):
        author_data = get_existing_magazine_author_by_id(author_data["duplicate of ID"], magazine_authors)

    return author_data


def get_contact_from_author_data(author_data):
    if not np.isnan(author_data["organization_name"]):
        contact = Organization.objects.get(
            drupal_author_id=author_data["drupal_author_id"]
        )
    elif not np.isnan(author_data["meeting_name"]):
        contact = Meeting.objects.get(drupal_author_id=author_data["drupal_author_id"])
    else:
        try:
            contact = Person.objects.get(
                drupal_author_id=author_data["drupal_author_id"]
            )
        except:
            print(
                "Cannot find person with ID:", f'"{ author_data["drupal_author_id"] }"'
            )

    return contact


def parse_article_authors(article, article_authors, magazine_authors):

    for drupal_author_id in article_authors.split(", "):
        drupal_author_id = int(drupal_author_id)

        author_data = get_existing_magazine_author_by_id(drupal_author_id, magazine_authors)

        author = get_contact_from_author_data(author_data)

    try:
        article_author = MagazineArticleAuthor(
            article=article,
            author=author,
        )

        article.authors.add(article_author)
    except:
        print("Could not create magazine article author.")
        pass

    return article


def assign_article_to_issue(article, issue_title):
    try:
        related_issue = MagazineIssue.objects.get(
            title=issue_title
        )
    except:
        print("Can't find issue: ", issue_title)

    related_issue.add_child(instance=article)


class Command(BaseCommand):
    help = "Import Articles from Drupal site while linking them to Authors, Issues, Deparments, and Keywords"

    def add_arguments(self, parser):
        parser.add_argument("--articles_file", action="store", type=str)
        # parser.add_argument("--authors_file", action="store", type=str)

    def handle(self, *args, **options):
        articles = pd.read_csv(options["articles_file"], dtype={"Authors": str})
        magazine_authors = pd.read_csv("../import_data/magazine_authors-2021-04-14-joined-authors_cleaned-deduped.csv")

        for index, row in tqdm(
            articles.iterrows(), total=articles.shape[0], desc="Articles", unit="row"
        ):

            department = MagazineDepartment.objects.get(title=row["Department"])

            article_body_blocks = []
            body_migrated = None

            if not np.isnan(row["Body"]):
                article_body_blocks = parse_article_body_blocks(row["Body"])
                body_migrated = row["Body"]

            # Download and parse article media
            if not np.isnan(row["Media"]):
                media_blocks = parse_media_blocks(row["Media"])

                # Merge media blocks with article body blocks
                article_body_blocks += media_blocks

            article = MagazineArticle(
                title=row["title"],
                body=article_body_blocks,
                body_migrated=body_migrated,
                department=department,
            )

            # Assign article to issue
            assign_article_to_issue(article, row["related_issue_title"])

            # Assign authors to article
            if not np.isnan(row["Authors"]):
                article = parse_article_authors(article, row["Authors"], magazine_authors)

            # Assign keywards to article
            if not np.isnan(row["Keywords"]):
                for keyword in row["Keywords"].split(", "):
                    article.tags.add(keyword)

            article.save()
