"""Conversion functions for converting HTML to Wagtail blocks."""

import re
from dataclasses import dataclass
from io import BytesIO
import logging

from bs4 import BeautifulSoup, Tag
from django.core.files.images import ImageFile
import requests
from wagtail.images.models import Image
from wagtail.rich_text import RichText
from content_migration.management.constants import SITE_BASE_URL

from content_migration.management.errors import (
    BlockFactoryError,
)

logger = logging.getLogger(__name__)

DEFAULT_IMAGE_WIDTH = 350
DEFAULT_IMAGE_ALIGN = "left"


@dataclass
class GenericBlock:
    block_type: str
    block_content: str


def convert_relative_image_url_to_absolute(image_url: str) -> str:
    """Convert a relative image URL to an absolute image URL."""
    if image_url is not None and image_url.startswith("/"):
        image_url = SITE_BASE_URL + image_url.lstrip("/")

    return image_url


def extract_image_urls(block_content: str) -> list[str]:
    """Get a list of all image URLs found within the block_content."""
    soup = BeautifulSoup(block_content, "html.parser")
    image_srcs = [img["src"] for img in soup.findAll("img")]
    return image_srcs


def extract_pullquotes(item: str) -> list[str]:
    """Get a list of all pullquote strings found within the item."""

    return re.findall(r"\[pullquote\](.+?)\[\/pullquote\]", item)


def remove_pullquote_tags(item_string: str) -> str:
    """Remove "[pullquote]" and "[/pullquote]" tags in string.

    https://stackoverflow.com/a/44593228/1191545
    """

    replacement_values: list = [
        ("[pullquote]", ""),
        ("[/pullquote]", ""),
    ]

    if item_string != "":
        for replacement_value in replacement_values:
            item_string = item_string.replace(*replacement_value)

    return item_string


def create_image_block(image_url: str) -> dict:
    """Create a Wagtial image block from an image URL."""

    try:
        response = requests.get(image_url)
    except requests.exceptions.MissingSchema:
        logger.error(f"Invalid image URL, missing schema: { image_url }")
        raise
    except requests.exceptions.InvalidSchema:
        logger.error(f"Invalid image URL, invalid schema: { image_url }")
        raise
    except requests.exceptions.RequestException:
        logger.error(f"Could not download image: { image_url }")
        raise

    file_bytes = BytesIO(response.content)

    # create an ImageFile object
    file_name = image_url.split("/")[-1]
    image_file = ImageFile(
        file_bytes,
        name=file_name,
    )

    # create and save a Wagtial image instance
    image = Image(
        title=file_name,
        file=image_file,
    )
    image.save()

    # Create an image block with dictionary properties
    image_chooser_block = {
        "image": image,
        "width": DEFAULT_IMAGE_WIDTH,
        "align": DEFAULT_IMAGE_ALIGN,
    }

    return image_chooser_block


class BlockFactory:
    """Factory class for creating Wagtail blocks."""

    @staticmethod
    def create_block(generic_block: GenericBlock) -> tuple[str, str | dict]:
        if generic_block.block_type == "rich_text":
            return (
                generic_block.block_type,
                RichText(generic_block.block_content),
            )
        elif generic_block.block_type == "image":
            try:
                image_block = create_image_block(generic_block.block_content)
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
                generic_block.block_content,
            )
        else:
            raise ValueError(f"Invalid block type: {generic_block.block_type}")


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
    for item in soup_contents:
        # skip non-Tag items
        if not isinstance(item, Tag):
            continue

        item_string = str(item)
        # skip empty items
        if item_string == "" or item_string is None:
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
                    )
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
                        )
                    )

                item_string = remove_pullquote_tags(item_string)

            if item_contains_image:
                image_urls = extract_image_urls(item_string)

                for image_url in image_urls:
                    image_url = convert_relative_image_url_to_absolute(image_url)

                    generic_blocks.append(
                        GenericBlock(
                            block_type="image",
                            block_content=image_url,
                        )
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
            )
        )

    return generic_blocks
