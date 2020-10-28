import re
from typing import List

from django.core.management.base import BaseCommand, CommandError

from bs4 import BeautifulSoup, Tag as BS4_Tag
import numpy as np
import pandas as pd

from wagtail.core.rich_text import RichText

from taggit.models import Tag

from magazine.models import (
    MagazineArticle,
    MagazineArticleAuthor,
    MagazineArticleTag,
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


class Command(BaseCommand):
    help = "Import Articles from Drupal site while linking them to Authors, Issues, Deparments, and Keywords"

    def add_arguments(self, parser):
        parser.add_argument("--articles_file", action="store", type=str)
        # parser.add_argument("--authors_file", action="store", type=str)

    def handle(self, *args, **options):
        articles = pd.read_csv(options["articles_file"])
        authors = pd.read_csv("../import_data/authors_cleaned_deduped-2020-04-12.csv")

        for index, row in articles.iterrows():

            department = MagazineDepartment.objects.get(title=row["Department"])

            article_body_blocks = []
            #article_body_blocks = parse_article_body_blocks(row["Body"])

            article = MagazineArticle(
                title=row["title"],
                body=article_body_blocks,
                body_migrated=row["Body"],
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
            for author in row["Authors"].split(", "):
                authors_mask = authors["drupal_full_name"] == author

                if authors_mask.sum() == 0:
                    print("Author not found:", author)
                if authors_mask.sum() > 1:
                    print("Duplicate authors found:", author)

                author_data = authors[authors_mask].iloc[0].to_dict()
                drupal_full_name = author_data["drupal_full_name"]

                if author_data["organization_name"] is not np.nan:
                    author = Organization.objects.get(
                        drupal_full_name=drupal_full_name
                    )
                elif author_data["meeting_name"] is not np.nan:
                    author = Meeting.objects.get(
                        drupal_full_name=drupal_full_name
                    )
                else:
                    try:
                        author = Person.objects.get(
                            drupal_full_name=drupal_full_name
                        )
                    except:
                        print("Cannot find person named:", f'"{ drupal_full_name }"')

                try:
                    article_author = MagazineArticleAuthor(article=article, author=author)
                    article.authors.add(article_author)
                except:
                    pass
                    #print("Could not assign author to article:", author, article)
            try:
                for keyword in row["Keywords"].split(", "):
                    article.tags.add(keyword)
            except:
                print("could not split: '", row["Keywords"], "'")

            article.save()
