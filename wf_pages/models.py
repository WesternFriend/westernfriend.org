from django.db import models
from django.http import HttpRequest

from modelcluster.fields import ParentalKey  # type: ignore
from modelcluster.contrib.taggit import ClusterTaggableManager  # type: ignore
from taggit.models import TaggedItemBase  # type: ignore
from wagtail import blocks as wagtail_blocks
from wagtail.admin.panels import FieldPanel
from wagtail.fields import RichTextField, StreamField
from wagtail.models import Page
from wagtail.search import index

from blocks.blocks import (
    FormattedImageChooserStructBlock,
    HeadingBlock,
    PullQuoteBlock,
    SpacerBlock,
)
from common.models import DrupalFields
from documents.blocks import DocumentEmbedBlock


class MollyWingateBlogIndexPage(Page):
    intro = RichTextField(blank=True)

    content_panels = Page.content_panels + [FieldPanel("intro")]

    parent_page_types = ["home.HomePage"]
    subpage_types: list[str] = ["wf_pages.MollyWingateBlogPage"]
    max_count = 1


class WfPageCollectionIndexPage(Page):
    intro = RichTextField(blank=True)

    content_panels = Page.content_panels + [FieldPanel("intro")]

    subpage_types: list[str] = ["wf_pages.WfPageCollection"]
    max_count = 1

    def get_context(self, request: HttpRequest, *args, **kwargs) -> dict:
        context = super().get_context(request)

        collections = WfPageCollection.objects.all()
        context["collections"] = collections

        return context


class WfPageCollection(Page):
    panels = [FieldPanel("title")]

    parent_page_types = ["wf_pages.WfPageCollectionIndexPage"]
    subpage_types: list[str] = []

    context_object_name = "collection"


class WfPageTag(TaggedItemBase):
    content_object = ParentalKey(
        "wf_pages.WfPage",
        on_delete=models.CASCADE,
        related_name="tagged_items",
    )


class WfPage(DrupalFields, Page):
    body = StreamField(
        [
            ("heading", HeadingBlock()),
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
                        "strikethrough",
                        "blockquote",
                    ]
                ),
            ),
            ("pullquote", PullQuoteBlock()),
            ("document", DocumentEmbedBlock()),
            ("image", FormattedImageChooserStructBlock(classname="full title")),
            ("spacer", SpacerBlock()),
        ],
        use_json_field=True,
    )
    body_migrated = models.TextField(
        help_text="Used only for content from old Drupal website.",
        null=True,
        blank=True,
    )
    drupal_node_id = models.IntegerField(
        help_text="Used only for content from old Drupal website.",
        null=True,
        blank=True,
    )
    collection = models.ForeignKey(
        WfPageCollection,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="pages",
    )
    tags = ClusterTaggableManager(
        through=WfPageTag,
        blank=True,
    )

    content_panels = Page.content_panels + [
        FieldPanel("body"),
        FieldPanel("collection"),
        FieldPanel("tags"),
    ]

    search_fields = Page.search_fields + [
        index.SearchField("body"),
        index.RelatedFields(
            "tags",
            [
                index.SearchField("name"),
            ],
        ),
    ]

    class Meta:
        verbose_name = "Page"
        verbose_name_plural = "Pages"


class MollyWingateBlogPage(DrupalFields, WfPage):
    publication_date = models.DateField("Publication date")

    content_panels = WfPage.content_panels + [
        FieldPanel("publication_date"),
    ]

    parent_page_types = ["wf_pages.MollyWingateBlogIndexPage"]
    subpage_types: list[str] = []

    class Meta:
        verbose_name = "Molly Wingate Blog Post"
        verbose_name_plural = "Molly Wingate Blog Posts"
