from collections import defaultdict

from django.db import models
from wagtail.admin.panels import FieldPanel
from wagtail.fields import RichTextField, StreamField
from wagtail.models import Page
from wagtail.search import index

from common.models import DrupalFields
from core.constants import COMMON_STREAMFIELD_BLOCKS

# Spec used by blocks/blocks/formatted_image_block.html.
BODY_IMAGE_RENDITION_SPEC = "width-800|jpegquality-80"


def _prefetch_streamfield_renditions(stream_value, *filter_specs: str) -> None:
    """Attach renditions to images already loaded on a StreamField.

    Image blocks bulk-load their images, then each ``{% image %}`` tag looks
    up its rendition. Setting ``prefetched_renditions`` makes that lookup use
    the images already in memory.
    """
    images = []
    for child in stream_value:
        if child.block_type != "image":
            continue
        image = child.value.get("image") if child.value else None
        if image is not None:
            images.append(image)
    if not images:
        return

    grouped: dict[int, list] = defaultdict(list)
    renditions = (
        images[0]
        .get_rendition_model()
        .objects.filter(
            image_id__in={image.pk for image in images},
            filter_spec__in=filter_specs,
        )
    )
    for rendition in renditions:
        grouped[rendition.image_id].append(rendition)
    for image in images:
        # An empty list still counts as prefetched, so a missing rendition
        # is created instead of queried once per image.
        image.prefetched_renditions = grouped.get(image.pk, [])


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
        # Use select_related to fetch publishing_meeting in a single query
        context["meeting_documents"] = (
            MeetingDocument.objects.live().public().select_related("publishing_meeting")
        )
        return context


class MeetingDocument(DrupalFields, Page):
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
        COMMON_STREAMFIELD_BLOCKS,
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

    search_fields = Page.search_fields + [
        index.SearchField("body"),
        index.RelatedFields(
            "publishing_meeting",
            [
                index.SearchField("title"),
            ],
        ),
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
    search_fields = Page.search_fields + [
        index.SearchField("intro"),
    ]

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        # category lives on the specific model, so order after .specific().
        documents = list(self.get_children().live().specific())
        documents.sort(key=lambda document: (document.category, document.path))
        context["documents"] = documents
        return context


class PublicBoardDocument(DrupalFields, Page):
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
        BOARD_MEMBERSHIP_ABOUT = (
            "board_membership_about",
            "Board Membership - About",
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
        COMMON_STREAMFIELD_BLOCKS,
        use_json_field=True,
    )

    parent_page_types = ["documents.PublicBoardDocumentIndexPage"]
    subpage_types: list[str] = []

    search_fields = Page.search_fields + [
        index.SearchField("body"),
    ]

    content_panels = Page.content_panels + [
        FieldPanel("category"),
        FieldPanel("publication_date"),
        FieldPanel("body"),
    ]

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        _prefetch_streamfield_renditions(self.body, BODY_IMAGE_RENDITION_SPEC)
        return context
