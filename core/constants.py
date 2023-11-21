from blocks.blocks import (
    FormattedImageChooserStructBlock,
    HeadingBlock,
    PullQuoteBlock,
    SpacerBlock,
)
from wagtail import blocks as wagtail_blocks
from documents.blocks import DocumentEmbedBlock

# StreamField Settings
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
            ],
        ),
    ),
    ("pullquote", PullQuoteBlock()),
    ("document", DocumentEmbedBlock()),
    ("image", FormattedImageChooserStructBlock(classname="full title")),
    ("spacer", SpacerBlock()),
]
