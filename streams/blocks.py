from django.core.validators import validate_slug
from django.forms.utils import flatatt
from django.utils.html import format_html, format_html_join
from wagtail.core import blocks
from wagtail.images.blocks import ImageChooserBlock

from wagtail_color_panel.blocks import NativeColorBlock
from wagtailmedia.blocks import AbstractMediaChooserBlock

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


class HeadingBlock(blocks.StructBlock):
    heading_level = blocks.ChoiceBlock(
        choices=[
            ("h2", "Level 2 (child of level 1)"),
            ("h3", "Level 3 (child of level 2)"),
            ("h4", "Level 4 (child of level 3)"),
            ("h5", "Level 5 (child of level 4)"),
            ("h6", "Level 6 (child of level 5)"),
        ],
        help_text="These different heading levels help to communicate the organization and hierarchy of the content on a page.",
    )
    heading_text = blocks.CharBlock(
        help_text="The text to appear in the heading.",
    )
    target_slug = blocks.CharBlock(
        help_text="Used to link to a specific location within this page. A slug should only contain letters, numbers, underscore (_), or hyphen (-).",
        validators=(validate_slug,),
        required=False,
    )
    color = NativeColorBlock(required=False,)

    class Meta:
        icon = "list-ol"
        template = "streams/blocks/heading.html"


class MediaBlock(AbstractMediaChooserBlock):
    def render_basic(self, value, context=None):
        if not value:
            return ""

        if value.type == "video":
            player_code = """
            <div>
                <video style="width:100%; height: 100%;" controls>
                    {0}
                    Your browser does not support the video tag.
                </video>
            </div>
            """
        else:
            player_code = """
            <div>
                <audio controls>
                    {0}
                    Your browser does not support the audio element.
                </audio>
            </div>
            """

        return format_html(
            player_code,
            format_html_join(
                "\n", "<source{0}>", [[flatatt(s)] for s in value.sources]
            ),
        )


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


class FormattedImageChooserStructBlock(blocks.StructBlock):
    image = ImageChooserBlock()
    width = blocks.IntegerBlock(
        min_value=0,
        max_value=800,
        help_text="Enter the desired image width value in pixels up to 800 max."
    )

    class Meta:
        icon = "media"
        template = "streams/blocks/formatted_image_block.html"
