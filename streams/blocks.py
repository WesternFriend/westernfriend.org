from django.utils.html import format_html
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
    page = blocks.PageChooserBlock(required=True)
    text = blocks.CharBlock(required=False)

    class Meta:
        icon = "link"
        template = "streams/blocks/page_card.html"


class OrganizationsBlock(blocks.StructBlock):

    def get_context(self, value, parent_context=None):
        # avoid circular imports
        from contact.models import Organization

        context = super().get_context(value, parent_context=parent_context)

        context["organizations"] = Organization.objects.all()

        return context

    class Meta:
        template = "streams/blocks/organizations_block.html"


class PullQuoteBlock(blocks.TextBlock):

    def render_basic(self, value, context=None):
        if value:
            return format_html('<div class="pullquote">{0}</div>', value)
        else:
            return ''

    class Meta:
        icon = "openquote"
