from io import BytesIO
import re
from typing import List

from django.core.files import File
from django.core.files.images import ImageFile
from django.core.management.base import BaseCommand, CommandError

from bs4 import BeautifulSoup, Tag as BS4_Tag
import numpy as np
import pandas as pd
import requests
from tqdm import tqdm

from wagtail.core.rich_text import RichText
from wagtail.documents.models import Document
from wagtail.images.models import Image


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


def parse_article_media_blocks(media_urls):
    media_blocks = []

    if media_urls is not np.nan:
        for url in media_urls.split(", "):
            response = requests.get(url)
            content_type = response.headers["content-type"]
            file_name = url.split("/")[-1]
            file_bytes = BytesIO(response.content)

            if content_type == "application/pdf":
                # Create file
                document_file = File(file_bytes, name=file_name)

                document = Document(title=file_name, file=document_file,)

                document.save()

                document_link_block = ("document", document)

                media_blocks.append(document_link_block)
            elif content_type in ["image/jpeg", "image/png"]:
                # create image
                image_file = ImageFile(file_bytes, name=file_name)

                image = Image(title=file_name, file=image_file,)

                image.save()

                image_block = ("image", image)

                media_blocks.append(image_block)
            else:
                print(url)
                print(content_type)
                print("-----")

    return media_blocks


class Command(BaseCommand):
    help = "Import Articles from Drupal site while linking them to Authors, Issues, Deparments, and Keywords"

    def add_arguments(self, parser):
        parser.add_argument("--articles_file", action="store", type=str)
        # parser.add_argument("--authors_file", action="store", type=str)

    def handle(self, *args, **options):
        articles = pd.read_csv(options["articles_file"])
        authors = pd.read_csv("../import_data/authors_cleaned_deduped-2020-04-12.csv")

        for index, row in tqdm(
            articles.iterrows(), total=articles.shape[0], desc="Articles", unit="row"
        ):
            media_blocks = parse_article_media_blocks(row["Media"])

            department = MagazineDepartment.objects.get(title=row["Department"])

            article_body_blocks = []
            body_migrated = None

            if row["Body"] is not np.nan:
                article_body_blocks = parse_article_body_blocks(row["Body"])
                body_migrated = row["Body"]

            # Download and parse article media
            media_blocks = parse_article_media_blocks(row["Media"])

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
                        author = Meeting.objects.get(drupal_full_name=drupal_full_name)
                    else:
                        try:
                            author = Person.objects.get(
                                drupal_full_name=drupal_full_name
                            )
                        except:
                            print(
                                "Cannot find person named:", f'"{ drupal_full_name }"'
                            )

                    try:
                        article_author = MagazineArticleAuthor(
                            article=article, author=author
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
