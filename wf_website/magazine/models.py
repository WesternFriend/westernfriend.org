import datetime
from datetime import timedelta

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db import models

from modelcluster.contrib.taggit import ClusterTaggableManager
from modelcluster.fields import ParentalKey
from taggit.models import TaggedItemBase

from wagtail.admin.edit_handlers import FieldPanel, InlinePanel, PageChooserPanel, MultiFieldPanel
from wagtail.core.models import Page, Orderable
from wagtail.core.fields import RichTextField
from wagtail.images.edit_handlers import ImageChooserPanel
from wagtail.search import index
from wagtail.snippets.edit_handlers import SnippetChooserPanel
from wagtail.snippets.models import register_snippet


class MagazineIndexPage(Page):
    intro = RichTextField(blank=True)

    content_panels = Page.content_panels + [
        FieldPanel('intro')
    ]

    subpage_types = [
        'MagazineIssue',
    ]

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request)

        # number of days for archive threshold
        archive_days_ago = 180

        # TODO: see if there is a better way to deal with
        # irregular month lengths for archive threshold
        archive_threshold = datetime.date.today() - timedelta(days=archive_days_ago)

        published_issues = MagazineIssue.objects.live().order_by('-publication_date')

        # recent issues are published after the archive threshold
        context['recent_issues'] = published_issues.filter(
            publication_date__gte=archive_threshold)

        archive_issues = published_issues.filter(
            publication_date__lt=archive_threshold)

        # Show three archive issues per page
        paginator = Paginator(archive_issues, 3)

        archive_issues_page = request.GET.get('archive-issues-page')

        try:
            paginated_archive_issues = paginator.page(archive_issues_page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            paginated_archive_issues = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            paginated_archive_issues = paginator.page(paginator.num_pages)

        # archive issues are published before the archive threshold
        context['archive_issues'] = paginated_archive_issues

        return context


class MagazineIssue(Page):
    cover_image = models.ForeignKey(
        'wagtailimages.Image',
        on_delete=models.SET_NULL,
        null=True,
        related_name='+',
    )
    publication_date = models.DateField(
        null=True,
        help_text="Please select the first day of the publication month",
    )

    @property
    def publication_end_date(self):
        if self.publication_date:
            # TODO: try to find a cleaner way to add a month to the publication date
            # I.e. the 'add a month' approach may be flawed altogether.
            return self.publication_date + timedelta(days=+31)

    content_panels = Page.content_panels + [
        FieldPanel('publication_date'),
        ImageChooserPanel('cover_image'),
        InlinePanel(
            'featured_articles',
            heading="Featured articles",
            help_text="Select one or more featured articles, from this issue",
        ),
    ]

    parent_page_types = [
        'MagazineIndexPage',
    ]
    subpage_types = [
        'MagazineArticle',
    ]

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request)

        context['articles_by_department'] = MagazineArticle.objects.child_of(self).live().order_by('department__name')

        return context

    def get_sitemap_urls(self):
        return [
            {
                'location': self.full_url,
                'lastmod': self.latest_revision_created_at
            }
        ]


class MagazineArticleTag(TaggedItemBase):
    content_object = ParentalKey(
        to='MagazineArticle',
        related_name='tagged_items',
        on_delete=models.CASCADE,
    )


class MagazineTagIndexPage(Page):
    def get_context(self, request, *args, **kwargs):
        tag = request.GET.get('tag')
        articles = MagazineArticle.objects.filter(tags__name=tag)

        context = super().get_context(request)
        context['articles'] = articles

        return context


class MagazineArticle(Page):
    body = RichTextField(blank=True)
    department = models.ForeignKey(
        'MagazineDepartment',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
    )
    tags = ClusterTaggableManager(through=MagazineArticleTag, blank=True)

    search_fields = Page.search_fields + [
        index.SearchField('body'),
    ]

    content_panels = Page.content_panels + [
        FieldPanel('body', classname="full"),
        MultiFieldPanel([
            SnippetChooserPanel('department'),
            FieldPanel('tags'),
        ], heading="Article information")
    ]

    parent_page_types = [
        'MagazineIssue',
    ]
    subpage_types = []

    def get_sitemap_urls(self):
        return [
            {
                'location': self.full_url,
                'lastmod': self.latest_revision_created_at,
                'priority': 1
            }
        ]


@register_snippet
class MagazineDepartment(models.Model):
    name = models.CharField(max_length=200)

    panels = [
        FieldPanel('name')
    ]

    def __str__(self):
        return self.name


class MagazineIssueFeaturedArticle(Orderable):
    issue = ParentalKey(
        'magazine.MagazineIssue',
        null=True,
        on_delete=models.CASCADE,
        related_name='featured_articles',
    )
    article = models.ForeignKey(
        MagazineArticle,
        null=True,
        on_delete=models.CASCADE,
        related_name='+',
    )

    panels = [
        PageChooserPanel('article')
    ]