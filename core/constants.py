from wagtail import blocks as wagtail_blocks
from blocks.blocks import (
    FormattedImageChooserStructBlock,
    HeadingBlock,
    PreformattedTextBlock,
    PullQuoteBlock,
    SpacerBlock,
)
from documents.blocks import DocumentEmbedBlock

STREAMFIELD_SETTINGS = [
    ("heading", HeadingBlock()),
    (
        "rich_text",
        wagtail_blocks.RichTextBlock(
            features=[
                "bold",
                "italic",
                "ol",
                "ul",
                "hr",
                "link",
                "document-link",
                "superscript",
                "superscript",
                "strikethrough",
                "blockquote",
            ],
        ),
    ),
    ("pullquote", PullQuoteBlock()),
    ("document", DocumentEmbedBlock()),
    ("image", FormattedImageChooserStructBlock(classname="full title")),
    ("spacer", SpacerBlock()),
    ("preformatted_text", PreformattedTextBlock()),
]
