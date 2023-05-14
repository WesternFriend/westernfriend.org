from django.db import models
from wagtail import blocks as wagtail_blocks
from wagtail.admin.panels import FieldPanel
from wagtail.models import Page
from wagtail.fields import StreamField, RichTextField
from documents.blocks import DocumentEmbedBlock

from blocks import blocks as wf_blocks


class PublicBoardDocumentIndexPage(Page):
    intro = RichTextField(
        blank=True,
        null=True,
        features=[
            "bold",
            "italic",
            "ol",
            "ul",
            "hr",
            "link",
        ],
    )

    parent_page_types = ["home.HomePage"]
    subpage_types = ["documents.PublicBoardDocument"]

    content_panels = Page.content_panels + [
        FieldPanel("intro", classname="full"),
    ]


class PublicBoardDocument(Page):
    class PublicBoardDocmentCategoryChoices(models.TextChoices):
        CORPORATION_DOCUMENTS_CURRENT_YEAR = (
            "corporation_documents_current_year",
            "Corporation Documents - current year",
        )
        CORPORATION_DOCUMENTS_PRIOR_YEARS = (
            "corporation_documents_prior_years",
            "Corporation Documents - prior years",
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
    category = models.CharField(
        choices=PublicBoardDocmentCategoryChoices.choices,
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
                DocumentEmbedBlock(),
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

    parent_page_types = ["documents.PublicBoardDocumentIndexPage"]
    subpage_types: list[str] = []

    content_panels = Page.content_panels + [
        FieldPanel("category"),
        FieldPanel("publication_date"),
        FieldPanel("body"),
    ]
