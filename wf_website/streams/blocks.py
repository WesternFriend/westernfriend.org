from wagtail.core import blocks
from wagtail.images.blocks import ImageChooserBlock

IMAGE_ALIGN_CHOICES = [
    ("left", "Left"),
    ("right", "Right"),
]


class ButtonBlock(blocks.StructBlock):
    button_text = blocks.CharBlock(required=False)
    page_link = blocks.PageChooserBlock(required=False)

    class Meta:
        icon = "placeholder"
        template = "streams/blocks/button.html"


class CardBlock(blocks.StructBlock):
    """Card with title, text, and image."""
    title = blocks.CharBlock(required=True, help_text="Add a title")
    text = blocks.RichTextBlock(required=False)
    image = ImageChooserBlock(required=False)
    image_align = blocks.ChoiceBlock(
        required=False,
        choices=IMAGE_ALIGN_CHOICES,
        default="left",
        help_text="Whether to align the image left or right on the block."
    )
    button = ButtonBlock(required=False)

    class Meta:
        icon = "form"
        template = "streams/blocks/card.html"


class PageCardBlock(blocks.StructBlock):
    text = blocks.CharBlock(required=False)
    page = blocks.PageChooserBlock(required=True)

    class Meta:
        icon = "link"
        template = "streams/blocks/page_card.html"
