import datetime

from defusedxml import ElementTree
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone
from wagtail.models import PageViewRestriction, Site

from contact.factories import PersonFactory
from magazine.factories import MagazineArticleFactory, MagazineIssueFactory
from magazine.feeds import FEED_ISSUE_COUNT
from magazine.models import MagazineArticleAuthor, MagazineIndexPage


class MagazineFeedTestCase(TestCase):
    def setUp(self) -> None:
        root = Site.objects.get(is_default_site=True).root_page
        self.magazine = MagazineIndexPage(title="Magazine")
        root.add_child(instance=self.magazine)

    def _issue(self, year: int, month: int, **kwargs):
        return MagazineIssueFactory(
            title=f"Issue {year}-{month:02d}",
            publication_date=datetime.date(year, month, 1),
            **kwargs,
        )

    def _items(self, url_name: str) -> list:
        response = self.client.get(reverse(url_name))
        self.assertEqual(response.status_code, 200)
        self.assertIn("application/rss+xml", response["Content-Type"])
        return ElementTree.fromstring(response.content).findall("./channel/item")


class MagazineIssueFeedTest(MagazineFeedTestCase):
    def test_lists_live_issues_newest_first(self) -> None:
        self._issue(2026, 8)
        self._issue(2026, 10)
        draft = self._issue(2026, 12)
        draft.unpublish()

        items = self._items("magazine_issue_feed")

        self.assertEqual(
            [item.findtext("title") for item in items],
            ["Issue 2026-10", "Issue 2026-08"],
        )
        self.assertIn("Oct 2026", items[0].findtext("pubDate"))

    def test_includes_issues_dated_ahead(self) -> None:
        # Issues often go up before the month on their cover.
        future = timezone.localdate() + datetime.timedelta(days=40)
        self._issue(future.year, future.month)

        titles = [i.findtext("title") for i in self._items("magazine_issue_feed")]

        self.assertEqual(titles, [f"Issue {future.year}-{future.month:02d}"])

    def test_is_limited_to_the_latest_issues(self) -> None:
        for month in range(1, FEED_ISSUE_COUNT + 3):
            self._issue(2025, month)

        self.assertEqual(len(self._items("magazine_issue_feed")), FEED_ISSUE_COUNT)


class MagazineArticleFeedTest(MagazineFeedTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.issue = self._issue(2026, 10)
        self.article = MagazineArticleFactory(
            title="Feed Article",
            teaser="<p>A short teaser.</p>",
            parent=self.issue,
        )
        author = PersonFactory(given_name="Ada", family_name="Writer")
        MagazineArticleAuthor.objects.create(article=self.article, author=author)

    def test_article_item_has_teaser_author_link_and_issue_date(self) -> None:
        (item,) = self._items("magazine_article_feed")

        self.assertEqual(item.findtext("title"), "Feed Article")
        self.assertIn("A short teaser.", item.findtext("description"))
        self.assertTrue(item.findtext("link").endswith(self.article.url))
        self.assertIn("01 Oct 2026", item.findtext("pubDate"))
        self.assertEqual(
            item.findtext("{http://purl.org/dc/elements/1.1/}creator"),
            "Ada Writer",
        )

    def test_never_includes_the_article_body(self) -> None:
        # Most articles are for subscribers; the feed carries the teaser only.
        body_text = str(self.article.body)[:40]
        response = self.client.get(reverse("magazine_article_feed"))

        self.assertTrue(body_text.strip())
        self.assertNotContains(response, body_text)

    def test_leaves_out_unpublished_and_private_articles(self) -> None:
        draft = MagazineArticleFactory(title="Draft Article", parent=self.issue)
        draft.unpublish()
        private = MagazineArticleFactory(title="Private Article", parent=self.issue)
        PageViewRestriction.objects.create(
            page=private,
            restriction_type=PageViewRestriction.LOGIN,
        )

        titles = [i.findtext("title") for i in self._items("magazine_article_feed")]

        self.assertEqual(titles, ["Feed Article"])

    def test_query_count_does_not_grow_with_articles(self) -> None:
        url = reverse("magazine_article_feed")
        with CaptureQueriesContext(connection) as one:
            self.client.get(url)
        for n in range(5):
            MagazineArticleFactory(title=f"More {n}", parent=self.issue)
        with CaptureQueriesContext(connection) as six:
            response = self.client.get(url)

        self.assertEqual(
            len(ElementTree.fromstring(response.content).findall("./channel/item")),
            6,
        )
        self.assertEqual(len(six), len(one))


class FeedDiscoveryTest(MagazineFeedTestCase):
    def test_pages_advertise_both_feeds(self) -> None:
        response = self.client.get(self.magazine.url)

        self.assertContains(
            response,
            f'<link rel="alternate" type="application/rss+xml" title="Western Friend magazine articles" href="{reverse("magazine_article_feed")}" />',
            html=False,
        )
        self.assertContains(response, reverse("magazine_issue_feed"))
