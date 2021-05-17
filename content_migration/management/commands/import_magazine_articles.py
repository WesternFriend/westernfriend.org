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


class Command(BaseCommand):
    help = "Import Articles from Drupal site while linking them to Authors, Issues, Deparments, and Keywords"

    def add_arguments(self, parser):
        parser.add_argument("--articles_file", action="store", type=str)
        # parser.add_argument("--authors_file", action="store", type=str)

    def handle(self, *args, **options):
        articles = pd.read_csv(options["articles_file"], dtype={"Authors": str})
        authors = pd.read_csv("../import_data/magazine_authors-2021-04-14-joined-authors_cleaned-deduped.csv")

        for index, row in tqdm(
            articles.iterrows(), total=articles.shape[0], desc="Articles", unit="row"
        ):

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
            )

            # Assign article to issue
            try:
                related_issue = MagazineIssue.objects.get(
                    title=row["related_issue_title"]
                )
            except:
                print("Can't find issue: ", row["related_issue_title"])
                print(row)

            related_issue.add_child(instance=article)

            # Assign authors to article
            if not row["Authors"] is np.nan:
                for drupal_author_id in row["Authors"].split(", "):
                    authors_mask = authors["drupal_author_id"] == int(drupal_author_id)

                    if authors_mask.sum() == 0:
                        print("Author not found:", drupal_author_id)
                    if authors_mask.sum() > 1:
                        print("Duplicate authors found:", drupal_author_id)

                    author_data = authors[authors_mask].iloc[0].to_dict()

                    if author_data["organization_name"] is not np.nan:
                        author = Organization.objects.get(
                            drupal_author_id=drupal_author_id
                        )
                    elif author_data["meeting_name"] is not np.nan:
                        author = Meeting.objects.get(drupal_author_id=drupal_author_id)
                    else:
                        try:
                            author = Person.objects.get(
                                drupal_author_id=drupal_author_id
                            )
                        except:
                            print(
                                "Cannot find person with ID:", f'"{ drupal_author_id }"'
                            )

                    try:
                        article_author = MagazineArticleAuthor(
                            article=article,
                            author=author,
                        )

                        article.authors.add(article_author)
                    except:
                        print("Could not create magazine article author.")
                        pass

            # Assign keywards to article
            if not row["Keywords"] is np.nan:
                for keyword in row["Keywords"].split(", "):
                    article.tags.add(keyword)

            article.save()
