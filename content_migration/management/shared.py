import csv
from dataclasses import dataclass
import html
from io import BytesIO
from itertools import chain
import logging
from urllib.parse import urlparse

from bs4 import BeautifulSoup
import requests
from django.core.files import File
from django.core.files.images import ImageFile
from django.db.models import Q
from wagtail.documents.models import Document
from wagtail.embeds.embeds import get_embed
from wagtail.embeds.models import Embed
from wagtail.images.models import Image

from contact.models import Meeting, Organization, Person
from content_migration.management.errors import (
    BlockFactoryError,
    CouldNotFindMatchingContactError,
    DuplicateContactError,
)
from content_migration.management.constants import (
    SITE_BASE_URL,
)
from content_migration.management.conversion import (
    adapt_html_to_generic_blocks,
    BlockFactory,
)

MEDIA_EMBED_DOMAINS = [
    "youtube.com",
    "www.youtube.com",
    "youtu.be",
    "www.youtu.be",
    "vimeo.com",
    "www.vimeo.com",
    "flickr.com",
    "www.flickr.com",
    "instagram.com",
    "www.instagram.com",
    "twitter.com",
    "www.twitter.com",
    "facebook.com",
    "www.facebook.com",
    "soundcloud.com",
    "www.soundcloud.com",
    "spotify.com",
    "www.spotify.com",
    "w.soundcloud.com",
    "player.vimeo.com",
    "open.spotify.com",
]


@dataclass
class FileBytesWithMimeType:
    file_bytes: BytesIO
    file_name: str
    content_type: str


logger = logging.getLogger(__name__)


def create_document_link_block(
    file_name: str,
    file_bytes: BytesIO,
) -> tuple[str, Document]:
    """Create a document link block from a file name and bytes.

    Returns a tuple of the form: ("document", document)
    """

    document_file: File = File(
        file_bytes,
        name=file_name,
    )

    document: Document = Document(
        title=file_name,
        file=document_file,
    )

    document.save()

    return ("document", document)


def create_media_embed_block(url: str) -> tuple[str, Embed]:
    """Create a media embed block from a URL
    Returns a tuple of the form: ("embed", embed)"""
    # TODO: add unit test, once database issues are sorted out
    embed: Embed = get_embed(url)

    embed_block = ("embed", embed)

    return embed_block


# TODO: remove this function,
def create_image_block(
    file_name: str,
    file_bytes: BytesIO,
) -> tuple[str, Image]:
    # create image
    image_file: ImageFile = ImageFile(
        file_bytes,
        name=file_name,
    )

    image = Image(
        title=file_name,
        file=image_file,
    )

    image.save()

    # Create an image block with dictionary properties
    # of FormattedImageChooserStructBlock
    media_item_block = (
        "image",
        {
            "image": image,
            "width": 800,
        },
    )

    return media_item_block


def fetch_file_bytes(url: str) -> FileBytesWithMimeType:
    """Fetch a file from a URL and return the file bytes."""

    try:
        response = requests.get(url)
    except requests.exceptions.RequestException:
        logger.error(f"Could not GET: '{ url }'")
        raise

    return FileBytesWithMimeType(
        file_bytes=BytesIO(response.content),
        file_name=html.unescape(url.split("/")[-1]),
        content_type=response.headers["content-type"],
    )


def parse_media_blocks(media_urls: list[str]) -> list[tuple]:
    media_blocks: list[tuple] = []

    for url in media_urls:
        if url == "":
            continue

        # Check if the URL starts with / and append the site base URL
        # ensuring there are not double // characters
        if url.startswith("/"):
            url = SITE_BASE_URL + url.lstrip("/")

        domain = urlparse(url).netloc

        if domain in MEDIA_EMBED_DOMAINS:
            embed_block = create_media_embed_block(url)
            media_blocks.append(embed_block)
        else:
            # The default should be to fetch a
            # PDF or image file (i.e. from westernfriend.org)

            try:
                fetched_file = fetch_file_bytes(url)
            except requests.exceptions.RequestException:
                continue

            if fetched_file.content_type == "application/pdf":
                media_item_block: tuple = create_document_link_block(
                    file_name=fetched_file.file_name,
                    file_bytes=fetched_file.file_bytes,
                )
            elif fetched_file.content_type in ["image/jpeg", "image/png"]:
                media_item_block = create_image_block(
                    file_name=fetched_file.file_name,
                    file_bytes=fetched_file.file_bytes,
                )
            else:
                logger.error(
                    f"Could not parse {fetched_file.content_type} media item: { url }"
                )
                continue

            media_blocks.append(media_item_block)

    return media_blocks


def get_existing_magazine_author_from_db(
    drupal_author_id: str | int,
) -> Person | Meeting | Organization:
    """Given a Drupal Author ID, Search across all types of contacts for a
    matching result. If the author is a duplicate, return the primary author
    record.

    Verify that any matches are unique.

    Return
    - the matching author or
    - None if no author was found.
    """
    # convert to int, if necessary
    drupal_author_id = int(drupal_author_id)

    # Query against primary drupal author ID column
    # Include a query to check `duplicate_author_ids` column,
    # since we are relying on that column to locate the "original" record
    # and the Library item authors data may reference duplicate authors
    person = Person.objects.filter(Q(drupal_author_id=drupal_author_id))
    meeting = Meeting.objects.filter(Q(drupal_author_id=drupal_author_id))
    organization = Organization.objects.filter(Q(drupal_author_id=drupal_author_id))

    results = list(chain(person, meeting, organization))

    if len(results) == 0:
        raise CouldNotFindMatchingContactError()
    elif len(results) > 1:
        logger.error(
            f"Duplicate authors found for magazine author ID: { int(drupal_author_id) }"
        )
        raise DuplicateContactError()
    else:
        return results[0]


def parse_csv_file(csv_file_path: str) -> list[dict]:
    """Parse a CSV file into a list of dictionaries."""
    with open(csv_file_path) as csv_file:
        csv_reader = csv.DictReader(csv_file)
        return list(csv_reader)


def create_group_by(group_by_key: str, items: list[dict]) -> dict:
    """Group a list of dictionaries by a key."""
    grouped_items: dict = {}

    for item in items:
        key = item[group_by_key]

        if key not in grouped_items:
            grouped_items[key] = []

        grouped_items[key].append(item)

    return grouped_items


def extract_image_urls(item: str) -> list[Image]:
    """Parse images from HTML string."""

    # parse images from HTML string containing <img> tags
    soup = BeautifulSoup(item, "html.parser")
    image_tags = soup.findAll("img")
    # Get a list of image URLs
    image_urls = [image_tag["src"] for image_tag in image_tags]

    return image_urls


def parse_body_blocks(body: str) -> list:
    article_body_blocks: list[tuple] = []

    generic_blocks = adapt_html_to_generic_blocks(body)

    for generic_block in generic_blocks:
        try:
            streamfield_block = BlockFactory.create_block(
                generic_block=generic_block,
            )
        except BlockFactoryError:
            continue

        article_body_blocks.append(streamfield_block)

    return article_body_blocks
