from dataclasses import dataclass
import logging

from bs4 import BeautifulSoup, Tag

from content_migration.management.commands.shared import extract_pullquotes

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


def create_image_block(block_content: str) -> str:
    image_urls = extract_image_urls(block_content)

    if len(image_urls) == 0:
        return ""

    # TODO: implement function to return Wagtial image block
    return ""


class BlockFactory:
    @staticmethod
    def create_block(generic_block: GenericBlock) -> tuple[str, str]:
        if generic_block.block_type == "rich_text":
            return (
                generic_block.block_type,
                generic_block.block_content,
            )
        elif generic_block.block_type == "image":
            return (
                generic_block.block_type,
                create_image_block(generic_block.block_content),
            )
        else:
            raise ValueError(f"Invalid block type: {generic_block.block_type}")


def adapt_html_to_generic_blocks(html_string: str) -> list[GenericBlock]:
    # parse the HTML string and return a list of GenericBlock objects
    # the function should be have exactly like the original parse_body_blocks
    # function, but instead of returning a list of tuples,
    # it should return a list of GenericBlock objects

    # Placeholder for gathering successive items
    rich_text_value = ""

    generic_blocks: list[GenericBlock] = []

    try:
        soup = BeautifulSoup(html_string, "html.parser")
    except TypeError:
        logger.error(f"Could not parse body: { html_string }")
        return generic_blocks

    for item in soup.findAll():
        # skip non-Tag items
        if not isinstance(item, Tag):
            continue

        item_string = str(item)
        # skip empty items
        if item_string == "":
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

            if item_contains_image:
                generic_blocks.append(
                    GenericBlock(
                        block_type="image",
                        block_content=item_string,
                    )
                )
        else:
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
