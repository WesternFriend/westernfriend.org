from wagtail.core import blocks
from wagtail.images.blocks import ImageChooserBlock


class CardBlock(blocks.StructBlock):
    """Card with title, text, and image."""
    title = blocks.CharBlock(required=True, help_text="Add a title")
    text = blocks.RichTextBlock(required=False)
    image = ImageChooserBlock(required=False)
    button_text = blocks.CharBlock(required=False)
    page_link = blocks.PageChooserBlock(requried=False)

    class Meta:
        icon = "form"
        template = 'streams/blocks/card.html'
