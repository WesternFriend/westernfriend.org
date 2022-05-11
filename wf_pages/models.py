from django.db import models

from wagtail.admin.edit_handlers import FieldPanel, StreamFieldPanel
from wagtail.core import blocks
from wagtail.core.fields import RichTextField, StreamField
from wagtail.core.models import Page
from wagtail.documents.blocks import DocumentChooserBlock
from wagtail.images.blocks import ImageChooserBlock

from documents.blocks import DocumentEmbedBlock
from streams.blocks import AnchorTarget


class WfPageCollectionIndexPage(Page):
    intro = RichTextField(blank=True)

    content_panels = Page.content_panels + [FieldPanel("intro")]

    subpage_types = ["wf_pages.WfPageCollection"]
    max_count = 1

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request)

        collections = WfPageCollection.objects.all()
        context["collections"] = collections

        return context


class WfPageCollection(Page):
    panels = [FieldPanel("title")]

    parent_page_types = ["wf_pages.WfPageCollectionIndexPage"]
    subpage_types = []

    context_object_name = "collection"


class WfPage(Page):
    body = StreamField(
        [
            ("document", DocumentEmbedBlock()),
            ("image", ImageChooserBlock()),
            (
                "paragraph",
                blocks.RichTextBlock(
                    features=[
                        "h2",
                        "h3",
                        "h4",
                        "bold",
                        "italic",
                        "ol",
                        "ul",
                        "hr",
                        "link",
                        "document-link",
                        "image",
                        "superscript",
                        "superscript",
                        "strikethrough",
                        "blockquote",
                    ]
                ),
            ),
            ("quote", blocks.BlockQuoteBlock()),
            ("target", AnchorTarget()),
        ]
    )
    body_migrated = models.TextField(
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

    content_panels = Page.content_panels + [
        StreamFieldPanel("body"),
        FieldPanel("collection"),
    ]

    class Meta:
        verbose_name = "Page"
        verbose_name_plural = "Pages"
