import datetime
from datetime import timedelta

from django.db import models
from django.db.models import QuerySet
from django.http import HttpRequest
from django_flatpickr.widgets import DatePickerInput
from modelcluster.contrib.taggit import ClusterTaggableManager  # type: ignore
from modelcluster.fields import ParentalKey  # type: ignore
from modelcluster.models import ClusterableModel  # type: ignore
from taggit.models import TaggedItemBase  # type: ignore
from wagtail.admin.panels import (
    FieldPanel,
    FieldRowPanel,
    HelpPanel,
    InlinePanel,
    MultiFieldPanel,
    PageChooserPanel,
)
from wagtail.fields import RichTextField, StreamField
from wagtail.models import Orderable, Page
from wagtail.search import index

from common.models import DrupalFields
from core.constants import STREAMFIELD_SETTINGS
from pagination.helpers import get_paginated_items

from .panels import NestedInlinePanel

MAGAZINE_ARCHIVE_THRESHOLD_DAYS = 180
ARCHIVE_THRESHOLD_DATE = datetime.date.today() - timedelta(
    days=MAGAZINE_ARCHIVE_THRESHOLD_DAYS,
)


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
            "deep_archive_page",
            page_type="magazine.DeepArchiveIndexPage",
        ),
        PageChooserPanel(
            "featured_deep_archive_issue",
            page_type="magazine.ArchiveIssue",
        ),
    ]

    subpage_types: list[str] = [
        "MagazineDepartmentIndexPage",
        "MagazineIssue",
        "MagazineTagIndexPage",
        "DeepArchiveIndexPage",
    ]

    max_count = 1

    def get_context(
        self,
        request: HttpRequest,
        *args: tuple,
        **kwargs: dict,
    ) -> dict:
        context = super().get_context(request)

        published_issues = MagazineIssue.objects.live().order_by("-publication_date")

        # recent issues are published after the archive threshold
        context["recent_issues"] = published_issues.filter(
            publication_date__gte=ARCHIVE_THRESHOLD_DATE,
        )

        archive_issues = published_issues.filter(
            publication_date__lt=ARCHIVE_THRESHOLD_DATE,
        )

        page_number = request.GET.get("page", "1")
        items_per_page = 8

        context["archive_issues"] = get_paginated_items(
            items=archive_issues,
            items_per_page=items_per_page,
            page_number=page_number,
        )

        return context


class MagazineIssue(DrupalFields, Page):  # type: ignore
    cover_image = models.ForeignKey(
        "wagtailimages.Image",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    publication_date = models.DateField(
        help_text="Please select the first day of the publication month",
        default=datetime.date.today,
    )
    issue_number = models.PositiveIntegerField(null=True, blank=True)
    drupal_node_id = models.PositiveIntegerField(null=True, blank=True, db_index=True)

    @property
    def featured_articles(self) -> QuerySet["MagazineArticle"]:
        # Return a cursor of related articles that are featured
        return (
            MagazineArticle.objects.child_of(self)
            .filter(is_featured=True)
            .specific()
            .prefetch_related("authors__author")
        )

    @property
    def articles_by_department(self) -> QuerySet["MagazineArticle"]:
        # Return a cursor of child articles ordered by department
        return (
            MagazineArticle.objects.child_of(self)
            .live()
            .order_by("department__title")
            .prefetch_related("authors__author")
        )

    @property
    def publication_end_date(self) -> datetime.date | None:
        """Return the first day of the month after the publication date.

        NOTE: we can return any day in the following month,
        since we only use the year and month components
        """

        # We add 31 days here since we can't add a month directly
        # 31 days is a safe upper bound for adding a month
        # since the publication date will be at least 28 days prior
        max_days_in_month = 31
        return self.publication_date + timedelta(days=+max_days_in_month)

    @property
    def is_public_access(self) -> bool:
        """Check whether issue should be accessible to all readers or only
        subscribers based on publication date and archive threshold."""

        # check whether publication date is before public access date
        return self.publication_date < ARCHIVE_THRESHOLD_DATE

    search_template = "search/magazine_issue.html"

    content_panels = Page.content_panels + [
        FieldPanel("publication_date", widget=DatePickerInput()),
        FieldPanel("cover_image"),
    ]

    parent_page_types = ["MagazineIndexPage"]
    subpage_types: list[str] = ["MagazineArticle"]

    class Meta:
        indexes = [
            models.Index(fields=["drupal_node_id"]),
        ]

    def get_sitemap_urls(self, changefreq=None, priority=None) -> list[dict]:
        return [
            {
                "location": self.full_url,
                "lastmod": self.latest_revision_created_at,
                "changefreq": changefreq,
            },
        ]


class MagazineArticleTag(TaggedItemBase):
    content_object = ParentalKey(
        to="MagazineArticle",
        related_name="tagged_items",
        on_delete=models.CASCADE,
    )


class MagazineTagIndexPage(Page):
    max_count = 1

    def get_context(
        self,
        request: HttpRequest,
        *args: tuple,
        **kwargs: dict,
    ) -> dict:
        tag = request.GET.get("tag")
        context = super().get_context(request)

        articles = MagazineArticle.objects.filter(
            tagged_items__tag__name=tag,
        ).live()
        context["articles"] = articles

        return context


class MagazineDepartmentIndexPage(Page):
    intro = RichTextField(blank=True)

    content_panels = Page.content_panels + [FieldPanel("intro")]

    parent_page_types = ["MagazineIndexPage"]
    subpage_types: list[str] = ["MagazineDepartment"]
    max_count = 1

    def get_context(
        self,
        request: HttpRequest,
        *args: tuple,
        **kwargs: dict,
    ) -> dict:
        departments = MagazineDepartment.objects.all()

        context = super().get_context(request)
        context["departments"] = departments

        return context


class MagazineDepartment(Page):
    content_panels = [FieldPanel("title")]

    # Hide the settings panels
    settings_panels: list[str] = []

    parent_page_types = ["MagazineDepartmentIndexPage"]
    subpage_types: list[str] = []

    # TODO: Determine whether we still use the autocomplete widget
    # Remove the following code if not using autocomplete
    autocomplete_search_field = "title"

    # TODO: remove if not using autocomplete
    def autocomplete_label(self) -> str:
        return self.title

    # TODO: remove if not using autocomplete
    def __str__(self) -> str:
        return self.title


class MagazineArticle(DrupalFields, Page):  # type: ignore
    teaser = RichTextField(  # type: ignore
        blank=True,
        help_text="Try to keep teaser to a couple dozen words.",
        features=[
            "bold",
            "italic",
            "link",
            "strikethrough",
        ],
    )
    body = StreamField(
        STREAMFIELD_SETTINGS,
        use_json_field=True,
    )
    is_featured = models.BooleanField(
        default=False,
        help_text="Feature this article in the related issue and allow full access without a subscription?",  # noqa: E501
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

    @classmethod
    def get_queryset(cls):
        """Prefetch authors and tags for performance."""
        related_fields = ["authors", "tags", "department"]
        return super().get_queryset().prefetch_related(*related_fields)

    class Meta:
        verbose_name = "Page"
        verbose_name_plural = "Pages"

    search_fields = Page.search_fields + [
        index.SearchField(
            "body",
        ),
    ]

    content_panels = Page.content_panels + [
        FieldPanel("teaser", classname="full"),
        FieldPanel("body"),
        InlinePanel(
            "authors",
            heading="Authors",
            help_text="Select one or more authors, who contributed to this article. Note: you must first add contacts in order to select them as authors.",  # noqa: E501
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
    subpage_types: list[str] = []

    def get_sitemap_urls(self, changefreq=None, priority=None) -> list[dict]:
        return [
            {
                "location": self.full_url,
                "lastmod": self.latest_revision_created_at,
                "changefreq": changefreq,
                "priority": 1,
            },
        ]

    @property
    def is_public_access(self) -> bool:
        """Check whether article should be accessible to all readers or only
        subscribers based on whether the issue is public access."""
        parent_issue = self.get_parent()

        return parent_issue.specific.is_public_access  # type: ignore

    def get_context(
        self,
        request: HttpRequest,
        *args: tuple,
        **kwargs: dict,
    ) -> dict:
        context = super().get_context(request)

        user_is_authenticated = False
        user_is_subscriber = False
        user_is_superuser = False

        # If user object is present in the request,
        # check for their authentication
        # and authorization status (subscriber or superuser authorization)
        if request.user is not None:
            user_is_authenticated = request.user.is_authenticated

            # Only check for subscriber and superuser status if user is authenticated,
            # preventing attribute errors on unauthenticated users
            if user_is_authenticated:
                user_is_subscriber = request.user.is_subscriber  # type: ignore
                user_is_superuser = request.user.is_superuser  # type: ignore

        # A user can view full article if
        # - they are a subscriber or a superuser,
        # - or if the article is marked as public access or featured
        context["user_can_view_full_article"] = (
            user_is_subscriber
            or user_is_superuser
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
            "author",
            ["contact.Person", "contact.Meeting", "contact.Organization"],
        ),
    ]

    class Meta:
        verbose_name = "Page"
        verbose_name_plural = "Pages"


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
            "author",
            ["contact.Person", "contact.Meeting", "contact.Organization"],
        ),
    ]

    class Meta:
        unique_together = ("article", "author")


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
        help_text="Page in the actual PDF file, when it differs from the original document",  # noqa: E501
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
            content="Add article authors by clicking the '+ Add' button below, if known.",  # noqa: E501
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


class ArchiveIssue(DrupalFields, Page):  # type: ignore
    publication_date = models.DateField(
        null=True,
        help_text="Please select the first day of the publication month",
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
            help_text="Add articles to the table of contents by clicking the '+ Add' button below",  # noqa: E501
        ),
    ]

    parent_page_types = ["DeepArchiveIndexPage"]
    subpage_types: list[str] = []

    class Meta:
        indexes = [
            models.Index(fields=["internet_archive_identifier"]),
        ]


class DeepArchiveIndexPage(Page):
    intro = RichTextField(blank=True)

    content_panels = Page.content_panels + [FieldPanel("intro")]

    max_count = 1

    parent_page_types = ["MagazineIndexPage"]
    subpage_types: list[str] = ["ArchiveIssue"]

    def get_publication_years(self) -> list[int]:
        publication_dates = ArchiveIssue.objects.dates("publication_date", "year")

        return [publication_date.year for publication_date in publication_dates]

    def get_filtered_archive_issues(
        self,
        query: dict[str, str],
    ) -> QuerySet[ArchiveIssue]:
        # Filter out any facet that isn't a model field
        allowed_keys = [
            "publication_date__year",
        ]

        facets = {
            f"{key}__icontains": query[key] for key in query if key in allowed_keys
        }

        return ArchiveIssue.objects.all().filter(**facets)

    def get_context(
        self,
        request: HttpRequest,
        *args: tuple,
        **kwargs: dict,
    ) -> dict:
        context = super().get_context(request, *args, **kwargs)

        query = request.GET.dict()

        archive_issues = self.get_filtered_archive_issues(
            query=query,  # type: ignore[arg-type]
        )

        page = request.GET.get("page", "1")
        items_per_page = 12

        context["archive_issues"] = get_paginated_items(
            items=archive_issues,
            items_per_page=items_per_page,
            page_number=page,
        )

        # Add publication years to context, for select menu
        context["publication_years"] = self.get_publication_years()

        return context
