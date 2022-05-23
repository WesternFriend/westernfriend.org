from django.core.exceptions import ObjectDoesNotExist
from contact.models import Meeting, Organization, Person
import html
from io import BytesIO
from urllib.parse import urlparse

from django.core.files import File
from django.core.files.images import ImageFile

from wagtail.documents.models import Document
from wagtail.embeds.embeds import get_embed
from wagtail.images.models import Image

import numpy as np
import pandas as pd
import requests


def parse_media_blocks(media_urls):
    media_blocks = []

    for url in media_urls.split(", "):
        domain = urlparse(url).netloc

        if domain in ["vimeo.com", "www.youtube.com"]:
            embed = get_embed(url)
            embed_tuple = ("embed", embed)
            media_blocks.append(embed_tuple)
        else:
            # The default should be to fetch a PDF or image file (i.e. from westernfriend.org)
            response = requests.get(url)
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

                # Create an image block with dictionary properties of FormattedImageChooserStructBlock
                image_block = ("image", {"image": image, "width": 800})

                media_blocks.append(image_block)
            else:
                print(url)
                print(content_type)
                print("-----")

    return media_blocks


def get_existing_magazine_author_by_id(drupal_author_id, magazine_authors):
    """
    Get an author and check if it is duplicate. Return existing author
    """
    authors_mask = magazine_authors["drupal_author_id"] == drupal_author_id

    if authors_mask.sum() == 0:
        print("Author not found:", drupal_author_id)
    if authors_mask.sum() > 1:
        print("Duplicate authors found:", drupal_author_id)

    author_data = None

    try:
        author_data = magazine_authors[authors_mask].iloc[0].to_dict()
    except:
        print("Could not get duplicate author data for author ID", drupal_author_id)

        return None

    # Get existing author, if this author is a duplicate
    if not pd.isnull(author_data["duplicate of ID"]):
        author_data = get_existing_magazine_author_by_id(
            author_data["duplicate of ID"], magazine_authors
        )

    return author_data


def get_contact_from_author_data(author_data):
    author_is_organization = not pd.isnull(author_data["organization_name"])

    author_is_meeting = not pd.isnull(author_data["meeting_name"])

    if author_is_organization:
        contact = Organization.objects.get(
            drupal_author_id=author_data["drupal_author_id"]
        )
    elif author_is_meeting:
        contact = Meeting.objects.get(drupal_author_id=author_data["drupal_author_id"])
    else:
        try:
            contact = Person.objects.get(
                drupal_author_id=author_data["drupal_author_id"]
            )
        except ObjectDoesNotExist:
            print(
                "Cannot find person with ID:", f'"{ author_data["drupal_author_id"] }"'
            )

        return contact
