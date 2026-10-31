"""RSS feeds for new magazine issues and their articles (#43)."""

import datetime

from django.contrib.syndication.views import Feed
from django.utils.feedgenerator import Rss201rev2Feed
from wagtail.rich_text import expand_db_html

from magazine.models import MagazineArticle, MagazineIndexPage, MagazineIssue

# Enough to cover a few months of issues, which is what a feed reader polling
# now and then needs; the full history is on the site.
FEED_ISSUE_COUNT = 6


def _issue_datetime(issue: MagazineIssue) -> datetime.datetime:
    """Feeds need a datetime; an issue only has a publication date."""
    return datetime.datetime.combine(
        issue.publication_date,
        datetime.time.min,
        tzinfo=datetime.UTC,
    )


def _latest_issues():
    # live() is the publication gate: issues are often dated ahead of the day
    # they go up, so the date alone doesn't say whether readers can see one.
    return (
        MagazineIssue.objects.live()
        .public()
        .order_by("-publication_date")[:FEED_ISSUE_COUNT]
    )


def _magazine_link() -> str:
    magazine = MagazineIndexPage.objects.live().first()
    return magazine.url if magazine else "/"


class MagazineIssueFeed(Feed):
    """The latest magazine issues, newest first."""

    feed_type = Rss201rev2Feed
    title = "Western Friend magazine issues"
    description = "New issues of Western Friend magazine."

    def link(self) -> str:
        return _magazine_link()

    def items(self):
        return _latest_issues()

    def item_title(self, item: MagazineIssue) -> str:
        return item.title

    def item_description(self, item: MagazineIssue) -> str:
        return item.publication_date.strftime("Western Friend, %B %Y")

    def item_link(self, item: MagazineIssue) -> str:
        return item.full_url

    def item_pubdate(self, item: MagazineIssue) -> datetime.datetime:
        return _issue_datetime(item)


class MagazineArticleFeed(Feed):
    """Articles from the latest issues, newest issue first.

    Each item carries the article's teaser, never its body: most articles
    are for subscribers, and the teaser is what the site already shows
    publicly in listings and search results.
    """

    feed_type = Rss201rev2Feed
    title = "Western Friend magazine articles"
    description = "Articles from the latest issues of Western Friend magazine."

    def link(self) -> str:
        return _magazine_link()

    def items(self):
        articles = []
        for issue in _latest_issues():
            articles.extend(
                MagazineArticle.objects.child_of(issue)
                .live()
                .public()
                .prefetch_related("authors__author"),
            )
        # One query for every parent issue, so item_pubdate costs nothing per item.
        MagazineArticle.prefetch_parent_issues(articles)
        return articles

    def item_title(self, item: MagazineArticle) -> str:
        return item.title

    def item_description(self, item: MagazineArticle) -> str:
        return expand_db_html(item.teaser)

    def item_link(self, item: MagazineArticle) -> str:
        return item.full_url

    def item_pubdate(self, item: MagazineArticle) -> datetime.datetime:
        return _issue_datetime(item.parent_issue)

    def item_author_name(self, item: MagazineArticle) -> str | None:
        names = [str(author.author) for author in item.authors.all()]
        return ", ".join(names) or None
