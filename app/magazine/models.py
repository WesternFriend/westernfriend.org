import datetime
from datetime import timedelta

import arrow
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db import models
from flatpickr import DatePickerInput
from modelcluster.contrib.taggit import ClusterTaggableManager
from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel
from taggit.models import TaggedItemBase
from wagtail import blocks as wagtail_blocks
from wagtail.admin.panels import (
    FieldPanel,
    FieldRowPanel,
    HelpPanel,
    InlinePanel,
    MultiFieldPanel,
    PageChooserPanel,
)
from wagtail.documents.blocks import DocumentChooserBlock
from wagtail.fields import RichTextField, StreamField
from wagtail.models import Orderable, Page
from wagtail.search import index

from blocks.blocks import (
    FormattedImageChooserStructBlock,
    HeadingBlock,
    PullQuoteBlock,
    SpacerBlock,
)

from .panels import NestedInlinePanel


class MagazineIndexPage(Page):
    intro = RichTextField(blank=True)
    deep_archive_intro = RichTextField(blank=True)
    deep_archive_page = models.ForeignKey(
        "magazine.DeepArchiveIndexPage",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    featured_deep_archive_issue = models.ForeignKey(
        "magazine.ArchiveIssue",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    content_panels = Page.content_panels + [
        FieldPanel("intro"),
        FieldPanel("deep_archive_intro"),
        PageChooserPanel(
            "deep_archive_page", page_type="magazine.DeepArchiveIndexPage"
        ),
        PageChooserPanel(
            "featured_deep_archive_issue", page_type="magazine.ArchiveIssue"
        ),
    ]

    subpage_types = [
        "MagazineDepartmentIndexPage",
        "MagazineIssue",
        "MagazineTagIndexPage",
        "DeepArchiveIndexPage",
    ]

    max_count = 1

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request)

        # number of days for archive threshold
        archive_days_ago = 180

        # TODO: see if there is a better way to deal with
        # irregular month lengths for archive threshold
        archive_threshold = datetime.date.today() - timedelta(days=archive_days_ago)

        published_issues = MagazineIssue.objects.live().order_by("-publication_date")

        # recent issues are published after the archive threshold
        context["recent_issues"] = published_issues.filter(
            publication_date__gte=archive_threshold
        )

        archive_issues = published_issues.filter(publication_date__lt=archive_threshold)

        # Show three archive issues per page
        paginator = Paginator(archive_issues, 8)

        archive_issues_page = request.GET.get("archive-issues-page")

        try:
            paginated_archive_issues = paginator.page(archive_issues_page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            paginated_archive_issues = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            paginated_archive_issues = paginator.page(paginator.num_pages)

        # archive issues are published before the archive threshold
        context["archive_issues"] = paginated_archive_issues

        return context


class MagazineIssue(Page):
    cover_image = models.ForeignKey(
        "wagtailimages.Image",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    publication_date = models.DateField(
        null=True, help_text="Please select the first day of the publication month"
    )
    issue_number = models.PositiveIntegerField(null=True, blank=True)

    @property
    def featured_articles(self):
        # Return a cursor of related articles that are featured
        return (
            MagazineArticle.objects.child_of(self).filter(is_featured=True).specific()
        )

    @property
    def publication_end_date(self):
        if self.publication_date:
            # TODO: try to find a cleaner way to add a month to the publication date
            # I.e. the 'add a month' approach may be flawed altogether.
            # Note: this should probably add more than one month,
            # since the magazine is not published monthly
            return self.publication_date + timedelta(days=+31)

    search_template = "search/magazine_issue.html"

    content_panels = Page.content_panels + [
        FieldPanel("publication_date", widget=DatePickerInput()),
        FieldPanel("cover_image"),
    ]

    parent_page_types = ["MagazineIndexPage"]
    subpage_types = ["MagazineArticle"]

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request)
        context["articles_by_department"] = (
            MagazineArticle.objects.child_of(self).live().order_by("department__title")
        )

        return context

    def get_sitemap_urls(self):
        return [{"location": self.full_url, "lastmod": self.latest_revision_created_at}]


class MagazineArticleTag(TaggedItemBase):
    content_object = ParentalKey(
        to="MagazineArticle", related_name="tagged_items", on_delete=models.CASCADE
    )


class MagazineTagIndexPage(Page):
    max_count = 1

    def get_context(self, request, *args, **kwargs):
        tag = request.GET.get("tag")
        articles = MagazineArticle.objects.filter(tags__name=tag)

        context = super().get_context(request)
        context["articles"] = articles

        return context


class MagazineDepartmentIndexPage(Page):
    intro = RichTextField(blank=True)

    content_panels = Page.content_panels + [FieldPanel("intro")]

    subpage_types = ["MagazineDepartment"]
    max_count = 1

    def get_context(self, request, *args, **kwargs):
        departments = MagazineDepartment.objects.all()

        context = super().get_context(request)
        context["departments"] = departments

        return context


class MagazineDepartment(Page):
    content_panels = [FieldPanel("title")]

    # Hide the settings panels
    settings_panels = []

    parent_page_types = ["MagazineDepartmentIndexPage"]
    subpage_types = []

    # TODO: Determine whether we still use the autocomplete widget
    # Remove the following code if not using autocomplete
    autocomplete_search_field = "title"

    # TODO: remove if not using autocomplete
    def autocomplete_label(self):
        return self.title

    # TODO: remove if not using autocomplete
    def __str__(self):
        return self.title


class MagazineArticle(Page):
    teaser = RichTextField(
        blank=True,
        help_text="Try to keep teaser to a couple dozen words.",
        features=[
            "bold",
            "italic",
            "link",
            "document-link",
            "strikethrough",
        ],
    )
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
                        "superscript",
                        "strikethrough",
                        "blockquote",
                    ]
                ),
            ),
            ("pullquote", PullQuoteBlock()),
            ("document", DocumentChooserBlock()),
            ("image", FormattedImageChooserStructBlock(classname="full title")),
            ("spacer", SpacerBlock()),
        ],
        use_json_field=True,
    )
    is_featured = models.BooleanField(
        default=False,
        help_text="Feature this article in the related issue and allow full access without a subscription?",
    )
    body_migrated = models.TextField(
        help_text="Used only for content from old Drupal website.",
        null=True,
        blank=True,
    )

    department = models.ForeignKey(
        MagazineDepartment,
        on_delete=models.PROTECT,
        related_name="articles",
    )

    tags = ClusterTaggableManager(through=MagazineArticleTag, blank=True)

    drupal_node_id = models.PositiveIntegerField(null=True, blank=True, db_index=True)

    search_template = "search/magazine_article.html"

    search_fields = Page.search_fields + [index.SearchField("body")]

    content_panels = Page.content_panels + [
        FieldPanel("teaser", classname="full"),
        FieldPanel("body"),
        FieldPanel("body_migrated", classname="full"),
        InlinePanel(
            "authors",
            heading="Authors",
            help_text="Select one or more authors, who contributed to this article. Note: you must first add contacts in order to select them as authors.",
            min_num=1,
        ),
        MultiFieldPanel(
            [
                PageChooserPanel("department", "magazine.MagazineDepartment"),
                FieldPanel("tags"),
                FieldPanel("is_featured"),
            ],
            heading="Article information",
        ),
    ]

    parent_page_types = ["MagazineIssue"]
    subpage_types = []

    def get_sitemap_urls(self):
        return [
            {
                "location": self.full_url,
                "lastmod": self.latest_revision_created_at,
                "priority": 1,
            }
        ]

    @property
    def is_public_access(self):
        """
        Check whether article should be accessible to all readers
        or only subscribers based on issue publication date.
        """
        parent_issue = self.get_parent()

        today = arrow.utcnow()

        six_months_ago = today.shift(months=-6).date()

        # Issues older than six months are public access
        return parent_issue.specific.publication_date <= six_months_ago

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request)

        # Check whether user is subscriber
        # make sure they are authenticated first,
        # to avoid checking for "is_subscriber" on anonymous user
        user_is_subscriber = (
            request.user.is_authenticated and request.user.is_subscriber
        )

        # Subscribers and superusers can always view full articles
        # everyone can view public access articles
        # everyone can view featured articles
        # user can view full article if any of these conditions is True
        context["user_can_view_full_article"] = (
            user_is_subscriber
            or request.user.is_superuser
            or self.is_public_access
            or self.is_featured
        )

        return context


class MagazineArticleAuthor(Orderable):
    article = ParentalKey(
        "magazine.MagazineArticle",
        on_delete=models.CASCADE,
        related_name="authors",
    )
    author = models.ForeignKey(
        "wagtailcore.Page",
        on_delete=models.CASCADE,
        related_name="articles_authored",
    )

    panels = [
        PageChooserPanel(
            "author", ["contact.Person", "contact.Meeting", "contact.Organization"]
        )
    ]


class ArchiveArticleAuthor(Orderable):
    article = ParentalKey(
        "magazine.ArchiveArticle",
        null=True,
        on_delete=models.CASCADE,
        related_name="archive_authors",
    )
    author = models.ForeignKey(
        "wagtailcore.Page",
        null=True,
        on_delete=models.CASCADE,
        related_name="archive_articles_authored",
    )

    panels = [
        PageChooserPanel(
            "author", ["contact.Person", "contact.Meeting", "contact.Organization"]
        )
    ]


class ArchiveArticle(ClusterableModel):
    title = models.CharField(max_length=255)
    issue = ParentalKey(
        "magazine.ArchiveIssue",
        null=True,
        on_delete=models.CASCADE,
        related_name="archive_articles",
    )
    # We record two page numbers
    # since the original documents used various page numbering schemes over time
    # and the PDF page number may differ from the original document
    toc_page_number = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Page number as it appears the original document",
    )
    pdf_page_number = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Page in the actual PDF file, when it differs from the original document",
    )
    drupal_node_id = models.PositiveIntegerField(null=True, blank=True)

    panels = [
        FieldPanel("title", classname="full"),
        FieldRowPanel(
            [
                FieldPanel("toc_page_number"),
                FieldPanel("pdf_page_number"),
            ],
            heading="Page numbers",
        ),
        HelpPanel(
            content="Add article authors by clicking the '+ Add' button below, if known."
        ),
        NestedInlinePanel(
            "archive_authors",
            heading="Authors",
            help_text="Select one or more authors who contributed to this article",
        ),
    ]

    class Meta:
        indexes = [
            models.Index(fields=["drupal_node_id"]),
        ]


class ArchiveIssue(Page):
    publication_date = models.DateField(
        null=True, help_text="Please select the first day of the publication month"
    )
    internet_archive_identifier = models.CharField(
        max_length=255,
        db_index=True,
        help_text="Identifier for Internet Archive item.",
        unique=True,
    )
    western_friend_volume = models.CharField(
        max_length=255,
        help_text="Related Western Friend volume.",
        null=True,
        blank=True,
    )

    content_panels = Page.content_panels + [
        FieldPanel("publication_date", widget=DatePickerInput()),
        FieldPanel("internet_archive_identifier"),
        FieldPanel("western_friend_volume"),
        InlinePanel(
            "archive_articles",
            heading="Table of contents",
            help_text="Add articles to the table of contents by clicking the '+ Add' button below",
        ),
    ]

    parent_page_types = ["DeepArchiveIndexPage"]
    subpage_types = []

    class Meta:
        indexes = [
            models.Index(fields=["internet_archive_identifier"]),
        ]


class DeepArchiveIndexPage(Page):
    intro = RichTextField(blank=True)

    content_panels = Page.content_panels + [FieldPanel("intro")]

    subpage_types = ["ArchiveIssue"]

    max_count = 1

    parent_page_types = ["MagazineIndexPage"]
    subpage_types = ["ArchiveIssue"]

    def get_publication_years(self):
        publication_dates = ArchiveIssue.objects.dates("publication_date", "year")

        return [publication_date.year for publication_date in publication_dates]

    def get_filtered_archive_issues(self, request):
        # Check if any query string is available
        query = request.GET.dict()

        # Filter out any facet that isn't a model field
        allowed_keys = [
            "publication_date__year",
        ]

        facets = {
            f"{key}__icontains": query[key] for key in query if key in allowed_keys
        }

        return ArchiveIssue.objects.all().filter(**facets)

    def get_paginated_archive_issues(self, archive_issues, request):
        items_per_page = 9

        paginator = Paginator(archive_issues, items_per_page)

        archive_issues_page = request.GET.get("page")

        try:
            paginated_archive_issues = paginator.page(archive_issues_page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            paginated_archive_issues = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            paginated_archive_issues = paginator.page(paginator.num_pages)

        return paginated_archive_issues

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request)

        archive_issues = self.get_filtered_archive_issues(request)

        paginated_archive_issues = self.get_paginated_archive_issues(
            archive_issues, request
        )

        context["archive_issues"] = paginated_archive_issues

        # Add publication years to context, for select menu
        context["publication_years"] = self.get_publication_years()

        return context
