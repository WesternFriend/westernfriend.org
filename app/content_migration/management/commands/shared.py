import html
from io import BytesIO
from itertools import chain
import re
from urllib.parse import urlparse

from bs4 import BeautifulSoup
from bs4 import Tag as BS4_Tag
import pandas as pd
import requests
from django.core.exceptions import ObjectDoesNotExist
from django.core.files import File
from django.core.files.images import ImageFile
from django.db.models import Q
from wagtail.documents.models import Document
from wagtail.embeds.embeds import get_embed
from wagtail.images.models import Image
from wagtail.rich_text import RichText

from contact.models import Meeting, Organization, Person


def extract_pullquotes(item: str) -> list[str]:
    """Get a list of all pullquote strings found within the item"""

    return re.findall(r"\[pullquote\](.+?)\[\/pullquote\]", item.string)


def clean_pullquote_tags(item: BS4_Tag) -> BS4_Tag:
    """
    Replace "[pullquote][/pullquote]" tags in string
    with "<span class='pullquote'></span>"
    https://stackoverflow.com/a/44593228/1191545
    """

    replacement_values = [
        ("[pullquote]", ""),
        ("[/pullquote]", ""),
    ]

    for replacement_value in replacement_values:
        item.string = item.string.replace(*replacement_value)

    return item


def parse_media_blocks(media_urls):
    media_blocks = []

    for url in media_urls.split(", "):
        domain = urlparse(url).netloc

        if domain in ["vimeo.com", "www.youtube.com"]:
            embed = get_embed(url)
            embed_tuple = ("embed", embed)
            media_blocks.append(embed_tuple)
        else:
            # The default should be to fetch a
            # PDF or image file (i.e. from westernfriend.org)

            try:
                response = requests.get(url)
            except:  # noqa: E722
                print(f"Could not GET: '{ url }'")
                continue

            content_type = response.headers["content-type"]
            file_name = html.unescape(url.split("/")[-1])
            file_bytes = BytesIO(response.content)

            if content_type == "application/pdf":
                # Create file
                document_file = File(file_bytes, name=file_name)

                document = Document(
                    title=file_name,
                    file=document_file,
                )

                document.save()

                document_link_block = ("document", document)

                media_blocks.append(document_link_block)
            elif content_type in ["image/jpeg", "image/png"]:
                # create image
                image_file = ImageFile(file_bytes, name=file_name)

                image = Image(
                    title=file_name,
                    file=image_file,
                )

                image.save()

                # Create an image block with dictionary properties
                # of FormattedImageChooserStructBlock
                image_block = ("image", {"image": image, "width": 800})

                media_blocks.append(image_block)
            else:
                print(url)
                print(content_type)
                print("-----")

    return media_blocks


def get_existing_magazine_author_from_db(drupal_author_id):
    """
    Given a Drupal Author ID,
    Search across all types of contacts for a matching result.
    If the author is a duplicate, return the primary author record.

    Verify that any matches are unique.

    Return
    - the matching author or
    - None if no author was found.
    """
    # Query against primary drupal author ID column
    # Include a query to check `duplicate_author_ids` column,
    # since we are relying on that column to locate the "original" record
    # and the Library item authors data may reference duplicate authors
    person = Person.objects.filter(
        Q(drupal_author_id=drupal_author_id)
        | Q(drupal_duplicate_author_ids__contains=[drupal_author_id])
    )
    meeting = Meeting.objects.filter(
        Q(drupal_author_id=drupal_author_id)
        | Q(drupal_duplicate_author_ids__contains=[drupal_author_id])
    )
    organization = Organization.objects.filter(
        Q(drupal_author_id=drupal_author_id)
        | Q(drupal_duplicate_author_ids__contains=[drupal_author_id])
    )

    results = list(chain(person, meeting, organization))

    magazine_author = None

    if len(results) == 0:
        print(f"Could not find magazine author by ID: { int(drupal_author_id) }")
    elif len(results) > 1:
        print(
            f"Duplicate authors found for magazine author ID: { int(drupal_author_id) }"
        )
    else:
        magazine_author = results[0]

    return magazine_author


def get_existing_magazine_author_by_id(
    drupal_author_id,
    magazine_authors,
):
    """Get an author and check if it is duplicate. Return existing author"""

    authors_mask = magazine_authors["drupal_author_id"] == drupal_author_id

    # Make sure author exists in data
    if authors_mask.sum() == 0:
        print("Author row not found in DataFrame:", drupal_author_id)
        return None

    # Make sure author is not in duplicate rows
    if authors_mask.sum() > 1:
        print("Duplicate DataFrame rows found with same author ID:", drupal_author_id)
        return None

    author_data = None

    try:
        author_data = magazine_authors[authors_mask].iloc[0].to_dict()
    except:  # noqa: E722
        print("Could not get author data for author ID:", drupal_author_id)

        return None

    # Get primary author row,
    # if this author row is marked as a duplicate
    if not pd.isnull(author_data["duplicate of ID"]):
        author_data = get_existing_magazine_author_by_id(
            author_data["duplicate of ID"],
            magazine_authors,
        )

    return author_data


def get_contact_from_author_data(author_data):
    contact = None

    author_is_organization = not pd.isnull(
        author_data["organization_name"],
    )

    author_is_meeting = not pd.isnull(
        author_data["meeting_name"],
    )

    if author_is_organization:
        try:
            contact = Organization.objects.get(
                drupal_author_id=author_data["drupal_author_id"]
            )
        except Organization.DoesNotExist:
            print(
                f"Could not find organization with ID: {author_data['drupal_author_id']}"  # noqa: E501
            )
    elif author_is_meeting:
        try:
            contact = Meeting.objects.get(
                drupal_author_id=author_data["drupal_author_id"],
            )
        except Meeting.DoesNotExist:
            print(f"Could not find meeting with ID: {author_data['drupal_author_id']}")
    else:
        try:
            contact = Person.objects.get(
                drupal_author_id=author_data["drupal_author_id"]
            )

        except ObjectDoesNotExist:
            print(
                "Could not find person with ID:",
                f'"{ author_data["drupal_author_id"] }"',
            )

    return contact


def parse_body_blocks(body):
    article_body_blocks = []

    try:
        soup = BeautifulSoup(body, "html.parser")
    except:  # noqa: E722
        soup = False

    # Placeholder for gathering successive items
    rich_text_value = ""

    if soup:
        for item in soup:

            item_has_value = item.string is not None

            if item_has_value:

                item_contains_pullquote = "pullquote" in item.string

                if item_contains_pullquote:
                    # Add current rich text value as rich text block, if not empty
                    if rich_text_value != "":
                        rich_text_block = ("rich_text", RichText(rich_text_value))

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
            rich_text_block = ("rich_text", RichText(rich_text_value))

            article_body_blocks.append(rich_text_block)

    return article_body_blocks
