from django.db import models
from wagtail import blocks as wagtail_blocks
from wagtail.admin.panels import FieldPanel
from wagtail.models import Page
from wagtail.fields import StreamField, RichTextField
from documents.blocks import DocumentEmbedBlock

from blocks import blocks as wf_blocks
from common.models import DrupalFields


class MeetingDocumentIndexPage(Page):
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
    subpage_types = ["documents.MeetingDocument"]

    content_panels = Page.content_panels + [
        FieldPanel("intro", classname="full"),
    ]

    def get_context(self, request):
        context = super().get_context(request)
        context["meeting_documents"] = MeetingDocument.objects.live().public()
        return context


class MeetingDocument(Page, DrupalFields):
    class MeetingDocmentTypeChoices(models.TextChoices):
        EPISTLE = (
            "epistle",
            "Epistle",
        )
        MINUTE = (
            "minute",
            "Minute of Concern",
        )
        PHOTOS = (
            "photos",
            "Photos",
        )

    publication_date = models.DateField()
    drupal_node_id = models.PositiveIntegerField(
        null=True,
        blank=True,
    )
    publishing_meeting = models.ForeignKey(
        "contact.Meeting",
        on_delete=models.PROTECT,
        related_name="published_documents",
    )
    document_type = models.CharField(
        choices=MeetingDocmentTypeChoices.choices,
        max_length=100,
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

    parent_page_types = ["documents.MeetingDocumentIndexPage"]
    subpage_types: list[str] = []

    content_panels = Page.content_panels + [
        FieldPanel("publishing_meeting"),
        FieldPanel("document_type"),
        FieldPanel("publication_date"),
        FieldPanel("body"),
    ]

    class Meta:
        ordering = [
            "-publication_date",
            "publishing_meeting",
            "document_type",
            "title",
        ]
        indexes = [
            models.Index(fields=["publication_date"]),
            models.Index(fields=["document_type"]),
        ]


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


class PublicBoardDocument(Page, DrupalFields):
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
        BOARD_PHOTOS = (
            "board_photos",
            "Board Photos",
        )

    publication_date = models.DateField()
    drupal_node_id = models.PositiveIntegerField(
        null=True,
        blank=True,
    )
    category = models.CharField(
        choices=PublicBoardDocmentCategoryChoices.choices,
        max_length=100,
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
