from django.db import models
from wagtail import blocks as wagtail_blocks
from wagtail.documents.blocks import DocumentChooserBlock
from wagtail.models import Page
from wagtail.fields import StreamField

from blocks import blocks as wf_blocks


class PublicBoardDocument(Page):
    class DocmentCategoryChoices(models.TextChoices):
        CORPORATION_DOCUMENTS = (
            "corporation_documents",
            "Corporation Documents",
        )
        ANNUAL_REPORTS = (
            "annual_reports",
            "Annual Reports",
        )
        RELATIONS_WITH_MONTHLY_MEETINGS = (
            "relations_with_monthly_meetings",
            "Relations with Monthly Meetings",
        )

    publication_date = models.DateField()
    drupal_node_id = models.PositiveIntegerField(
        null=True,
        blank=True,
    )
    category = models.TextField(
        choices=DocmentCategoryChoices.choices,
    )
    body = StreamField(
        [
            (
                "heading",
                wf_blocks.HeadingBlock(),
            ),
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
                    ]
                ),
            ),
            (
                "pullquote",
                wf_blocks.PullQuoteBlock(),
            ),
            (
                "document",
                DocumentChooserBlock(),
            ),
            (
                "image",
                wf_blocks.FormattedImageChooserStructBlock(
                    classname="full title",
                ),
            ),
            (
                "spacer",
                wf_blocks.SpacerBlock(),
            ),
        ],
        use_json_field=True,
    )
