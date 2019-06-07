from django.db import models

from wagtail.admin.edit_handlers import (
    FieldPanel,
    InlinePanel,
    MultiFieldPanel,
    PageChooserPanel,
    StreamFieldPanel,
)
from wagtail.core.models import Orderable, Page
from wagtail.core.fields import RichTextField, StreamField
from wagtail.core import blocks
from wagtail.documents.blocks import DocumentChooserBlock
from wagtail.embeds.blocks import EmbedBlock
from wagtail.images.blocks import ImageChooserBlock

from modelcluster.fields import (
    ParentalKey,
)

AUDIENCE_CHOICES = (
    ("hs_and_older", "HS and older"),
    ("intergenerational", "Intergenerational"),
    ("grades_k-5", "Grades K-5"),
    ("grades_6-10", "Grades 6-10"),
)

GENRE_CHOICES = (
    ("biography", "Biography"),
    ("commentary", "Commentary"),
    ("documentary", "Documentary"),
    ("epistle", "Epistle"),    
    ("exposition", "Exposition"),
    ("fiction", "Fiction"),
    ("history", "History"),
    ("humor", "Humor"),
    ("keynote_talk", "Keynote Talk"),
    ("lesson_plan", "Lesson Plan"),
    ("memorial_minute", "Memorial Minute"),
    ("narrative", "Narrative"),
    ("poetry", "Poetry"),
    ("prayer", "Prayer"),
    ("reference", "Reference"),   
)

MEDIUM_CHOICES = (
    ("audio", "Audio production"),
    ("blog", "Blog"),
    ("drawing_painting", "Drawing/Painting"),
    ("photograph", "Photograph"),
    ("print", "Print document"),
    ("video", "Video production"),
    ("website", "Website"),
)

TIME_PERIOD_CHOICES = (
    ("timeless", "Timeless"),
    ("1400s", "1400s"),
    ("1500s", "1500s"),
    ("1600s", "1600s"),
    ("1700s", "1700s"),
    ("1800s", "1800s"),
    ("1900s", "1900s"),
    ("2000s", "2000s"),
)

TOPIC_CHOICES = (
    ("community", "Community"),
    ("equality", "Equality"),
    ("good_order_in_quaker_meetings", "Good Order in Quaker Meetings"),
    ("integrity", "Integrity"),
    ("the_light", "The Light"),
    ("peace", "Peace"),
    ("simplicity", "Simplicity"),
    ("stewardship", "Stewardship"),
    ("quaker_camps", "Quaker Camps"),
    ("quaker_culture", "Quaker Culture"),
    ("quaker_public_policy_organizations", "Quaker Public Policy Organizations"),
    ("quaker_publishers", "Quaker Publishers"),
    ("quaker_retreat_centers", "Quaker Retreat Centers"),
    ("quaker_schools", "Quaker Schools"),
    ("quaker_service_organizations", "Quaker Service Organizations"),
)

class LibraryItem(Page):
    publication_date = models.DateField("Publication date")
    body = StreamField(
        [
            ("paragraph", blocks.RichTextBlock()),
            ("image", ImageChooserBlock()),
            ("document", DocumentChooserBlock()),
            ("embed", EmbedBlock()),
            ("url", blocks.URLBlock()),
            ("quote", blocks.BlockQuoteBlock()),
        ]
    )

    content_panels = Page.content_panels + [
        InlinePanel(
            "authors",
            heading="Authors",
            help_text="Select one or more authors, who contributed to this article",
        ),
        FieldPanel("publication_date"),
        StreamFieldPanel("body"),
    ]

    parent_page_types = ["LibraryIndexPage"]
    subpage_types = []


class LibraryItemAuthor(Orderable):
    library_item = ParentalKey(
        "library.LibraryItem",
        null=True,
        on_delete=models.CASCADE,
        related_name="authors",
    )
    author = models.ForeignKey(
        "wagtailcore.Page", null=True, on_delete=models.CASCADE, related_name="library_items_authored"
    )

    panels = [
        PageChooserPanel(
            "author",
            [
                "contact.Person",
                "contact.Meeting",
                "contact.Organization",
            ]
        )
    ]



class LibraryIndexPage(Page):
    intro = RichTextField(blank=True)

    content_panels = Page.content_panels + [FieldPanel("intro")]

    # parent_page_types = ["home.HomePage"]
    subpage_types = ["LibraryItem"]

    max_count = 1
