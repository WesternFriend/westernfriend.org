"""Shared functions for content migration."""

import csv
import html
import logging
from dataclasses import dataclass
from io import BytesIO
from itertools import chain
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup, Tag
from django.core.files import File
from django.core.files.images import ImageFile
from django.db.models import Q
from wagtail.contrib.redirects.models import Redirect
from wagtail.documents.models import Document
from wagtail.embeds.embeds import get_embed
from wagtail.embeds.models import Embed
from wagtail.images.models import Image
from wagtail.models import Page
from wagtail.rich_text import RichText
from wagtailmedia.models import Media  # type: ignore

from contact.models import Meeting, Organization, Person

from content_migration.management.errors import (
    BlockFactoryError,
    CouldNotFindMatchingContactError,
    CouldNotParseAuthorIdError,
    DuplicateContactError,
)
from content_migration.management.constants import (
    DEFAULT_IMAGE_ALIGN,
    DEFAULT_IMAGE_WIDTH,
    IMPORT_FILENAMES,
    LOCAL_MIGRATION_DATA_DIRECTORY,
    SITE_BASE_URL,
)
from store.models import Book, BookAuthor

ALLOWED_AUDIO_CONTENT_TYPES = [
    "audio/mpeg",
    "audio/mp4",
    "audio/ogg",
    "audio/wav",
    "audio/webm",
]

ALLOWED_DOCUMENT_CONTENT_TYPES = [
    "application/pdf",
]

ALLOWED_IMAGE_CONTENT_TYPES = [
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/svg+xml",
    "image/webp",
]

EMPTY_ITEM_VALUES = [
    "",
    "~",
    "&nbsp;",
    " ",
    None,
]


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


def get_or_create_site_root_page() -> Page:
    root_page: Page
    try:
        root_page = Page.objects.get(
            id=1,
        )
    except Page.DoesNotExist:
        root_page = Page.objects.create(
            id=1,
        ).save()

    return root_page


def get_or_create_book_author(
    book: Book,
    drupal_author_id: int,
) -> BookAuthor:
    """Create a BookAuthor object from a Book and a Drupal author ID."""
    author = get_existing_magazine_author_from_db(drupal_author_id=drupal_author_id)

    book_author_exists = BookAuthor.objects.filter(
        book=book,
        author=author,
    ).exists()

    if book_author_exists:
        return BookAuthor.objects.get(
            book=book,
            author=author,
        )
    else:
        book_author = BookAuthor(
            book=book,
            author=author,
        )

        book_author.save()

        return book_author


def construct_import_file_path(file_key: str) -> str:
    """Construct the path to a file to import."""
    return f"{LOCAL_MIGRATION_DATA_DIRECTORY}{IMPORT_FILENAMES[file_key]}"


@dataclass
class FileBytesWithMimeType:
    """A dataclass for holding file bytes and a MIME type."""

    file_bytes: BytesIO
    file_name: str
    content_type: str


logging.basicConfig(
    filename="import_shared.log",
    level=logging.ERROR,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)


@dataclass
class ArchiveIssueData:
    internet_archive_identifier: str
    archive_articles: list[dict]


@dataclass
class GenericBlock:
    """Generic block dataclass that represents a Wagtail block tuple."""

    block_type: str
    block_content: str | dict


@dataclass
class GenericFormattedImageBlock:
    """Generic block dataclass that represents a Wagtail block tuple."""

    image_url: str
    link_url: str | None


def create_image_block_from_url(
    image_url: str,
    link_url: str | None = None,
    align: str | None = None,
) -> dict:
    """Create a Wagtial image block from an image URL."""

    file_bytes = get_file_bytes_from_url(file_url=image_url)

    # create an ImageFile object
    file_name = image_url.split(sep="/")[-1]
    image = create_image_from_file_bytes(
        file_name=file_name,
        file_bytes=file_bytes,
    )

    # Create an image block with dictionary properties
    image_chooser_block = {
        "image": image,
        "width": DEFAULT_IMAGE_WIDTH,
        "align": align,
        "link": link_url,
    }

    return image_chooser_block


class BlockFactory:
    """Factory class for creating Wagtail blocks."""

    @staticmethod
    def create_block(generic_block: GenericBlock) -> tuple[str, str | dict]:
        if generic_block.block_type == "rich_text":
            return (
                generic_block.block_type,
                RichText(generic_block.block_content),  # type: ignore
            )
        elif generic_block.block_type == "image":
            image_url: str = generic_block.block_content["image"]  # type: ignore
            link_url: str | None = (
                generic_block.block_content["link"]  # type: ignore
                if generic_block.block_content["link"] is not None  # type: ignore
                else None
            )
            align: str = (
                generic_block.block_content["align"]  # type: ignore
                if generic_block.block_content["align"] is not None  # type: ignore
                else DEFAULT_IMAGE_ALIGN
            )
            try:
                image_block = create_image_block_from_url(
                    image_url=image_url,
                    link_url=link_url,  # type: ignore
                    align=align,  # type: ignore
                )
            except requests.exceptions.MissingSchema:
                raise BlockFactoryError("Invalid image URL: missing schema")
            except requests.exceptions.InvalidSchema:
                raise BlockFactoryError("Invalid image URL: invalid schema")
            return (
                generic_block.block_type,
                image_block,
            )
        elif generic_block.block_type == "pullquote":
            return (
                generic_block.block_type,
                str(generic_block.block_content),
            )
        else:
            raise ValueError(f"Invalid block type: {generic_block.block_type}")


def get_file_bytes_from_url(file_url: str) -> BytesIO:
    """Get file bytes from a URL."""

    try:
        response = requests.get(file_url)
    except requests.exceptions.MissingSchema:
        logger.error(f"Invalid URL, missing schema: { file_url }")
        raise
    except requests.exceptions.InvalidSchema:
        logger.error(f"Invalid URL, invalid schema: { file_url }")
        raise
    except requests.exceptions.RequestException:
        logger.error(f"Could not download file: { file_url }")
        raise

    return BytesIO(response.content)


def get_or_create_image(
    image_url: str,
) -> Image:
    """Get or create an image from an image URL."""

    # Check if the image already exists
    file_name = image_url.split(sep="/")[-1]

    image_exists = Image.objects.filter(title=file_name).exists()

    if image_exists:
        return Image.objects.get(title=file_name)
    else:
        # Download the image
        file_bytes = get_file_bytes_from_url(file_url=image_url)

        # create an ImageFile object
        return create_image_from_file_bytes(
            file_name=file_name,
            file_bytes=file_bytes,
        )


def remove_pullquote_tags(item_string: str) -> str:
    """Remove the span with class 'pullquote' from a string, preserving the
    contents of the span.

    Note:
    There may be multiple pullquotes in a string.

    Warning:
    There could be other spans that we don't want to remove, so we
    need to be careful to only remove the pullquote spans.
    """

    # Remove the pullquote spans
    soup = BeautifulSoup(item_string, "html.parser")
    for pullquote in soup.find_all("span", {"class": "pullquote"}):
        pullquote.unwrap()

    return str(soup)


def get_image_align_from_style(style_string: str) -> str | None:
    """Get the image alignment from the style string."""

    if "float:left" in style_string or "float: left" in style_string:
        return "left"
    elif "float:right" in style_string or "float: right" in style_string:
        return "right"
    else:
        return DEFAULT_IMAGE_ALIGN


def adapt_html_to_generic_blocks(html_string: str) -> list[GenericBlock]:
    """Adapt HTML string to a list of generic blocks."""

    generic_blocks: list[GenericBlock] = []

    try:
        soup = BeautifulSoup(html_string, "html.parser")
    except TypeError:
        logger.error(f"Could not parse body: { html_string }")
        return generic_blocks

    # Placeholder for gathering successive items
    rich_text_value = ""
    soup_contents = soup.contents
    for soup_item in soup_contents:
        # skip non-Tag items
        if not isinstance(soup_item, Tag):
            continue

        item_string = str(soup_item)
        # skip empty items
        if item_string in EMPTY_ITEM_VALUES:
            continue

        item_contains_pullquote = "pullquote" in item_string
        item_contains_image = "img" in item_string

        if item_contains_pullquote or item_contains_image:
            # store the accumulated rich text value
            # if it is not empty
            # and then reset the rich text value
            if rich_text_value != "":
                generic_blocks.append(
                    GenericBlock(
                        block_type="rich_text",
                        block_content=rich_text_value,
                    ),
                )

                # reset rich text value
                rich_text_value = ""

            if item_contains_pullquote:
                pullquotes = extract_pullquotes(item_string)

                for pullquote in pullquotes:
                    generic_blocks.append(
                        GenericBlock(
                            block_type="pullquote",
                            block_content=pullquote,
                        ),
                    )

                item_string = remove_pullquote_tags(item_string)

            if item_contains_image:
                # use beautiful soup to get an iterable of image Tag objects
                image_tags = soup_item.find_all("img")

                for image_tag in image_tags:
                    # check if image tag has a src attribute
                    if "src" not in image_tag.attrs:
                        continue

                    # get image src
                    image_url = image_tag["src"]
                    image_url = ensure_absolute_url(image_url)

                    # get image alignment from style attribute float property
                    if "style" in image_tag.attrs:
                        image_style = image_tag["style"]
                        image_align = get_image_align_from_style(image_style)
                    else:
                        image_align = DEFAULT_IMAGE_ALIGN

                    # make sure the URL contains westernfriend.org
                    if "westernfriend.org" not in image_url:
                        raise ValueError(
                            f"Image URL must contain westernfriend.org: {image_url}",
                        )

                    # check if image is wrapped in a link
                    if image_tag.parent.name == "a":
                        image_link_url = image_tag.parent["href"]
                    else:
                        image_link_url = None

                    image_chooser_block_content = {
                        "image": image_url,
                        "link": image_link_url,
                        "align": image_align,
                    }

                    generic_blocks.append(
                        GenericBlock(
                            block_type="image",
                            block_content=image_chooser_block_content,
                        ),
                    )

                    # reset item string,
                    # since the image block has been created
                    # and we don't expect any more blocks
                    item_string = ""

        if item_string != "":
            rich_text_value += item_string

    # store the accumulated rich text value
    # if it is not empty
    if rich_text_value != "":
        generic_blocks.append(
            GenericBlock(
                block_type="rich_text",
                block_content=rich_text_value,
            ),
        )

    return generic_blocks


def create_document_from_file_bytes(
    file_name: str,
    file_bytes: BytesIO,
) -> Document:
    """Create a document from a file name and bytes."""

    document_file: File = File(
        file_bytes,
        name=file_name,
    )

    document: Document = Document(
        title=file_name,
        file=document_file,
    )

    document.save()

    return document


def create_document_link_block(
    file_name: str,
    file_bytes: BytesIO,
) -> tuple[str, Document]:
    """Create a document link block from a file name and bytes.

    Returns a tuple of the form: ("document", document)
    """

    document = create_document_from_file_bytes(
        file_name=file_name,
        file_bytes=file_bytes,
    )

    return ("document", document)


def create_image_from_file_bytes(
    file_name: str,
    file_bytes: BytesIO,
) -> Image:
    """Create an image from a file name and bytes."""

    image_file: ImageFile = ImageFile(
        file_bytes,
        name=file_name,
    )

    image: Image = Image(
        title=file_name,
        file=image_file,
    )

    image.save()

    return image


def create_media_embed_block(url: str) -> tuple[str, Embed]:
    """Create a media embed block from a URL
    Returns a tuple of the form: ("embed", embed)"""
    # TODO: add unit test, once database issues are sorted out
    embed: Embed = get_embed(url)

    embed_block = ("embed", embed)

    return embed_block


def create_image_block_from_file_bytes(
    file_name: str,
    file_bytes: BytesIO,
) -> tuple[str, dict]:
    """Create an image block from a file name and bytes.

    Returns a tuple of the form: ("image", image_block)
    """

    image = create_image_from_file_bytes(
        file_name=file_name,
        file_bytes=file_bytes,
    )

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


def create_media_from_file_bytes(
    file_name: str,
    file_bytes: BytesIO,
    file_type: str,
) -> Media:
    """Create a media item from a file name and bytes."""

    media_file: File = File(
        file_bytes,
        name=file_name,
    )

    media: Media = Media(
        title=file_name,
        file=media_file,
        type=file_type,
    )

    media.save()

    return media


def create_media_block_from_file_bytes(
    file_name: str,
    file_bytes: BytesIO,
    file_type: str,
) -> tuple[str, Media]:
    """Create a media item block from a file name and bytes.

    Returns a tuple of the form: ("media", media_block)
    """

    media = create_media_from_file_bytes(
        file_name=file_name,
        file_bytes=file_bytes,
        file_type=file_type,
    )

    # Create a media item block with dictionary properties
    # of AbstractMediaChooserBlock
    media_block = (
        "media",
        media,
    )

    return media_block


def extract_pullquotes(item: str) -> list[str]:
    """Get a list of all pullquote strings found within the item, excluding the
    pullquote spans.

    The pullquote strings are wrapped in a span with class 'pullquote'.

    Example:
    <span class="pullquote">This is a pullquote</span>
    Will return:
    ["This is a pullquote"]

    Returns a list of pullquote strings.
    """

    pullquotes = []

    soup = BeautifulSoup(item, "html.parser")
    for pullquote in soup.find_all("span", {"class": "pullquote"}):
        # within the pullquote span, there may be other HTML tags
        # e.g. <span class="pullquote">This is a <strong>pullquote</strong></span>
        # so we need to get the string of the pullquote span
        # without the HTML tags
        pullquote_string = pullquote.get_text()
        pullquotes.append(pullquote_string)

    return pullquotes


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


def parse_media_string_to_list(media_string: str) -> list[str]:
    """Parse a media string to a list of media URLs."""

    media_urls = media_string.split(", ")

    # Remove empty strings
    media_urls = list(filter(None, media_urls))

    return media_urls


def ensure_absolute_url(url: str) -> str:
    """Ensure that the URL is absolute and belongs to the WesternFriend.org
    domain.

    Example:
    /media/images/image.jpg

    Will be converted to:
    https://<site_base_url>/media/images/image.jpg
    """

    # Check if the URL starts with / and append the site base URL
    # ensuring there are not double // characters
    if url.startswith("/"):
        url = SITE_BASE_URL + url.lstrip("/")

    return url


def extract_image_urls(block_content: str) -> list[str]:
    """Get a list of all image URLs found within the block_content."""
    soup = BeautifulSoup(block_content, "html.parser")
    image_srcs = [img["src"] for img in soup.findAll("img")]
    return image_srcs


def parse_media_blocks(media_urls: list[str]) -> list[tuple]:
    """Given a list of media URLs, return a list of media blocks."""

    media_blocks: list[tuple] = []

    for url in media_urls:
        if url == "":
            continue

        url = ensure_absolute_url(url)

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

            if fetched_file.content_type in ALLOWED_DOCUMENT_CONTENT_TYPES:
                media_item_block: tuple = create_document_link_block(
                    file_name=fetched_file.file_name,
                    file_bytes=fetched_file.file_bytes,
                )
            elif fetched_file.content_type in ALLOWED_IMAGE_CONTENT_TYPES:
                media_item_block = create_image_block_from_file_bytes(
                    file_name=fetched_file.file_name,
                    file_bytes=fetched_file.file_bytes,
                )
            elif fetched_file.content_type in ALLOWED_AUDIO_CONTENT_TYPES:
                media_item_block = create_media_block_from_file_bytes(
                    file_name=fetched_file.file_name,
                    file_bytes=fetched_file.file_bytes,
                    file_type="audio",
                )
            else:
                logger.error(
                    f"Could not parse {fetched_file.content_type} media item: { url }",
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
    try:
        drupal_author_id = int(drupal_author_id)
    except ValueError:
        raise CouldNotParseAuthorIdError()

    # Query against primary drupal author ID column
    # Include a query to check `duplicate_author_ids` column,
    # since we are relying on that column to locate the "original" record
    # and the Library item authors data may reference duplicate authors
    person = Person.objects.filter(Q(drupal_author_id=drupal_author_id))
    meeting = Meeting.objects.filter(Q(drupal_author_id=drupal_author_id))
    organization = Organization.objects.filter(Q(drupal_author_id=drupal_author_id))

    results = list(chain(person, meeting, organization))  # type: ignore

    if len(results) == 0:
        error_message = f"Could not find matching author for magazine author ID: { int(drupal_author_id) }"  # noqa: E501
        logger.error(error_message)

        raise CouldNotFindMatchingContactError(error_message)
    elif len(results) > 1:
        error_message = (
            f"Duplicate authors found for magazine author ID: { int(drupal_author_id) }"
        )
        logger.error(error_message)
        raise DuplicateContactError(error_message)
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


def create_archive_issues_from_articles_dicts(
    articles: list[dict],
) -> list[ArchiveIssueData]:
    """Create ArchiveIssue objects from a list of article dictionaries."""

    # Group articles by issue
    issues = create_group_by("internet_archive_identifier", articles)

    archive_issues: list[ArchiveIssueData] = []

    for issue in issues:
        issue_data = ArchiveIssueData(
            internet_archive_identifier=issue,
            archive_articles=issues[issue],
        )
        archive_issues.append(issue_data)

    return archive_issues


def parse_body_blocks(body: str) -> list:
    """Parse the body field into a list of StreamField blocks."""
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


def create_permanent_redirect(
    redirect_path: str,
    redirect_entity: Page,
) -> None:
    """Create a permanent redirect from the old path to the new page."""

    redirect_exists = Redirect.objects.filter(old_path=redirect_path).exists()

    if not redirect_exists:
        Redirect.objects.create(
            old_path=redirect_path,  # the old path from Drupal
            site=redirect_entity.get_site(),
            redirect_page=redirect_entity,  # the new page
            is_permanent=True,
        ).save()
