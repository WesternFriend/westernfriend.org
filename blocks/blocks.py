from django.core.validators import validate_slug
from django import forms
from django.forms.utils import flatatt
from django.utils.html import format_html, format_html_join
from wagtail import blocks as wagtail_blocks
from wagtail.images.blocks import ImageChooserBlock
from wagtail_color_panel.blocks import NativeColorBlock
from wagtailmedia.blocks import AbstractMediaChooserBlock

# TODO: convert to a models.TextChoices class
IMAGE_ALIGN_CHOICES = [
    ("left", "Left"),
    ("right", "Right"),
]


class ButtonBlock(wagtail_blocks.StructBlock):
    button_text = wagtail_blocks.CharBlock(required=False)
    page_link = wagtail_blocks.PageChooserBlock(required=False)

    class Meta:
        icon = "placeholder"
        template = "blocks/blocks/button.html"


class CardBlock(wagtail_blocks.StructBlock):
    """Card with title, text, and image."""

    title = wagtail_blocks.CharBlock(required=True, help_text="Add a title")
    text = wagtail_blocks.RichTextBlock(required=False)
    image = ImageChooserBlock(required=False)
    image_align = wagtail_blocks.ChoiceBlock(
        required=False,
        choices=IMAGE_ALIGN_CHOICES,
        default="left",
        help_text="Whether to align the image left or right on the block.",
    )
    button = ButtonBlock(required=False)

    class Meta:
        icon = "form"
        template = "blocks/blocks/card.html"


class FormattedImageChooserStructBlock(wagtail_blocks.StructBlock):
    image = ImageChooserBlock()
    width = wagtail_blocks.IntegerBlock(
        min_value=0,
        max_value=800,
        help_text="Enter the desired image width value in pixels up to 800 max.",
    )
    align = wagtail_blocks.ChoiceBlock(
        help_test="Optionally align image left or right. Will default to block alignment.",  # noqa: E501
        choices=(
            ("left", "Left"),
            ("right", "Right"),
        ),
        default=None,
        required=False,
        icon="file-richtext",
    )
    link = wagtail_blocks.URLBlock(
        required=False,
        help_text="Optional web address to use as image link.",
    )

    class Meta:
        icon = "media"
        template = "blocks/blocks/formatted_image_block.html"


class HeadingBlock(wagtail_blocks.StructBlock):
    heading_level = wagtail_blocks.ChoiceBlock(
        choices=[
            ("h2", "Level 2 (child of level 1)"),
            ("h3", "Level 3 (child of level 2)"),
            ("h4", "Level 4 (child of level 3)"),
            ("h5", "Level 5 (child of level 4)"),
            ("h6", "Level 6 (child of level 5)"),
        ],
        help_text="These different heading levels help to communicate the organization and hierarchy of the content on a page.",  # noqa: E501
    )
    heading_text = wagtail_blocks.CharBlock(
        help_text="The text to appear in the heading.",
    )
    target_slug = wagtail_blocks.CharBlock(
        help_text="Used to link to a specific location within this page. A slug should only contain letters, numbers, underscore (_), or hyphen (-).",  # noqa: E501
        validators=(validate_slug,),
        required=False,
    )
    color = NativeColorBlock(
        required=False,
    )

    class Meta:
        icon = "list-ol"
        template = "blocks/blocks/heading.html"


class MediaBlock(AbstractMediaChooserBlock):
    def render_basic(self, value, context=None):
        if not value:
            return ""

        if value.type == "video":
            player_code = """
            <div>
                <video width="{1}" height="{2}" controls>
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
                "\n",
                "<source{0}>",
                [[flatatt(s)] for s in value.sources],
            ),
            value.width,
            value.height,
        )


class PageCardBlock(wagtail_blocks.StructBlock):
    page = wagtail_blocks.PageChooserBlock(required=True)
    text = wagtail_blocks.CharBlock(required=False)

    class Meta:
        icon = "link"
        template = "blocks/blocks/page_card.html"


class PullQuoteBlock(wagtail_blocks.TextBlock):
    def render_basic(self, value: str, context=None) -> str:
        if value != "" and value is not None:
            return format_html('<div class="pullquote">{0}</div>', value)
        return ""

    class Meta:
        icon = "openquote"


class SpacerBlock(wagtail_blocks.StructBlock):
    height = wagtail_blocks.DecimalBlock(
        help_text="The height of this spacer in 'em' values where 1 em is one uppercase M.",  # noqa: E501
        min_value=0,
        decimal_places=1,
    )

    class Meta:
        icon = "arrows-up-down"
        template = "blocks/blocks/spacer.html"


class WfURLBlock(wagtail_blocks.URLBlock):
    class Meta:
        template = "blocks/blocks/wf_url.html"


class PreformattedTextBlock(wagtail_blocks.FieldBlock):
    """Renders input as preformatted text (<pre> tag)"""

    class Meta:
        template = "blocks/blocks/preformatted_text.html"

    def __init__(self, required=True, help_text=None, **kwargs):
        self.field = forms.CharField(
            required=required,
            help_text=help_text,
            widget=forms.Textarea(attrs={"rows": 10}),
        )
        super().__init__(**kwargs)
