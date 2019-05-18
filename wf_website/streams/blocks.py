from wagtail.core import blocks
from wagtail.images.blocks import ImageChooserBlock

IMAGE_ALIGN_CHOICES = [
    ("left", "Left"),
    ("right", "Right"),
]


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
    button_text = blocks.CharBlock(required=False)
    page_link = blocks.PageChooserBlock(requried=False)

    class Meta:
        icon = "form"
        template = 'streams/blocks/card.html'
