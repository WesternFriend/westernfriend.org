from wagtail import blocks as wagtail_blocks
from wagtail.embeds.blocks import EmbedBlock
from blocks.blocks import (
    FormattedImageChooserStructBlock,
    HeadingBlock,
    PayPalDonationButtonBlock,
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
                "embed",
            ],
        ),
    ),
    ("pullquote", PullQuoteBlock()),
    ("document", DocumentEmbedBlock()),
    ("image", FormattedImageChooserStructBlock(classname="full title")),
    ("spacer", SpacerBlock()),
    ("preformatted_text", PreformattedTextBlock()),
    ("embed", EmbedBlock(max_width=800, max_height=400)),
    ("paypal_donate_button", PayPalDonationButtonBlock()),
]
