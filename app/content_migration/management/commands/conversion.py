import re
from dataclasses import dataclass
from io import BytesIO
import logging

from bs4 import BeautifulSoup, Tag
from django.core.files.images import ImageFile
import requests
from wagtail.images.models import Image

from content_migration.management.commands.errors import (
    BlockFactoryError,
)

logger = logging.getLogger(__name__)


@dataclass
class GenericBlock:
    block_type: str
    block_content: str


def extract_image_urls(block_content: str) -> list[str]:
    # extract image src URLs from HTML string
    soup = BeautifulSoup(block_content, "html.parser")
    image_srcs = [img["src"] for img in soup.findAll("img")]
    return image_srcs


def extract_pullquotes(item: str) -> list[str]:
    """Get a list of all pullquote strings found within the item"""

    return re.findall(r"\[pullquote\](.+?)\[\/pullquote\]", item)


def remove_pullquote_tags(item_string: str) -> str:
    """
    Remove "[pullquote]" and "[/pullquote]" tags in string

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
    # download file bytes
    # create an ImageFile object
    # create a Wagtial image block
    #
    # return Wagtial image block

    # download file bytes with requests
    try:
        response = requests.get(image_url)
    except requests.exceptions.RequestException:
        logger.error(f"Could not download image: { image_url }")
        raise
    except (requests.exceptions.MissingSchema, requests.exceptions.InvalidSchema):
        logger.error(f"Invalid image URL: { image_url }")
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

    # Create a dictionary with properties
    # of FormattedImageChooserStructBlock
    image_chooser_block = {
        "image": image,
        "width": 800,
    }

    return image_chooser_block


class BlockFactory:
    @staticmethod
    def create_block(generic_block: GenericBlock) -> tuple[str, str | dict]:
        if generic_block.block_type == "rich_text":
            return (
                generic_block.block_type,
                generic_block.block_content,
            )
        elif generic_block.block_type == "image":
            try:
                image_block = create_image_block(generic_block.block_content)
            except requests.exceptions.MissingSchema:
                raise BlockFactoryError("Invalid image URL: missing schema")
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
    # parse the HTML string and return a list of GenericBlock objects
    # the function should be have exactly like the original parse_body_blocks
    # function, but instead of returning a list of tuples,
    # it should return a list of GenericBlock objects

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
