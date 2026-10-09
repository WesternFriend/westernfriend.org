from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import validate_slug
from django.utils.html import format_html
from wagtail import blocks as wagtail_blocks
from wagtail.documents.blocks import DocumentChooserBlock
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
    caption = wagtail_blocks.CharBlock(
        required=False,
        help_text="Optional caption (tooltip) to display with the image.",
    )
    width = wagtail_blocks.IntegerBlock(
        min_value=0,
        max_value=800,
        help_text="Enter the desired image width value in pixels up to 800 max.",
    )
    align = wagtail_blocks.ChoiceBlock(
        help_test="Optionally align image left or right. Will default to block alignment.",
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
        help_text="These different heading levels help to communicate the organization and hierarchy of the content on a page.",
    )
    heading_text = wagtail_blocks.CharBlock(
        help_text="The text to appear in the heading.",
    )
    target_slug = wagtail_blocks.CharBlock(
        help_text="Used to link to a specific location within this page. A slug should only contain letters, numbers, underscore (_), or hyphen (-).",
        validators=(validate_slug,),
        required=False,
    )
    color = NativeColorBlock(
        required=False,
    )

    class Meta:
        icon = "list-ol"
        template = "blocks/blocks/heading.html"


CAPTIONS_NOT_VTT_ERROR = (
    "Captions must be a WebVTT (.vtt) file. '%(filename)s' is not a .vtt file."
)


def validate_webvtt_document(document) -> None:
    """Reject a captions document that is not a WebVTT (.vtt) file.

    Without this, any document the editor picks is rendered as a caption
    ``<track>``: a PDF or an image produces a track the browser cannot parse,
    so the captions silently never appear.
    """
    if document.file_extension.lower() != "vtt":
        raise ValidationError(
            CAPTIONS_NOT_VTT_ERROR,
            code="invalid_caption_format",
            params={"filename": document.filename},
        )


class MediaChooserBlock(AbstractMediaChooserBlock):
    """Concrete media chooser used inside :class:`MediaBlock`.

    The player markup is rendered by ``MediaBlock``'s template, not here, so
    that an optional caption ``<track>`` can sit *inside* the ``<video>`` /
    ``<audio>`` element where the browser expects it.

    It still returns the media title rather than nothing, because
    ``MediaChooserBlockComparison`` feeds ``render_basic`` into the revision
    comparison view: returning an empty string leaves the Media row blank
    there even when the media has been swapped, while its sibling captions and
    transcript rows show their change.
    """

    def render_basic(self, value, context=None) -> str:
        if not value:
            return ""
        return format_html("{}", value.title)


class MediaBlock(wagtail_blocks.StructBlock):
    """Audio or video with an optional caption track and transcript.

    Captions (a WebVTT file) and a text transcript make uploaded media usable
    by Deaf and hard-of-hearing readers (WCAG 1.2.1, 1.2.2, 1.2.3, 1.2.5).
    """

    media = MediaChooserBlock()
    captions = DocumentChooserBlock(
        required=False,
        validators=(validate_webvtt_document,),
        help_text=(
            "Optional WebVTT (.vtt) caption file, shown on the player. "
            "Captions for embedded YouTube or Vimeo videos are set with the "
            "provider, not here."
        ),
    )
    transcript = wagtail_blocks.RichTextBlock(
        required=False,
        help_text=(
            "Optional text transcript, shown beneath the player so the content "
            "is available without audio."
        ),
    )

    class Meta:
        icon = "media"
        label = "Media"
        template = "blocks/blocks/media.html"


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
        help_text="The height of this spacer in 'em' values where 1 em is one uppercase M.",
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

    def __init__(self, *, required=True, help_text=None, **kwargs):
        self.field = forms.CharField(
            required=required,
            help_text=help_text,
            widget=forms.Textarea(attrs={"rows": 10}),
        )
        super().__init__(**kwargs)
