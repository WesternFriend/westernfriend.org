"""Tests for excluding individual magazine articles from AI use."""

from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse
from wagtail.models import Locale, Page, Site

from accounts.models import User
from common.ai_preferences import AI_CRAWLER_USER_AGENTS
from home.models import HomePage
from navigation.models import NavigationMenuSetting

from .models import (
    MagazineArticle,
    MagazineDepartment,
    MagazineDepartmentIndexPage,
    MagazineIndexPage,
    MagazineIssue,
)

EXCLUDED_PATH = "/magazine/issue/excluded/"
INCLUDED_PATH = "/magazine/issue/included/"


def robots_groups(content):
    """Split robots.txt into groups of lines, keyed by their first user agent."""
    groups = {}
    for block in content.strip().split("\n\n"):
        lines = block.splitlines()
        if lines[0].startswith("User-agent: "):
            groups[lines[0].removeprefix("User-agent: ")] = lines
    return groups


class ArticleAIOptOutTest(TestCase):
    def setUp(self):
        Locale.objects.get_or_create(language_code="en")
        Site.objects.all().delete()
        root = Page.get_first_root_node() or Page.add_root(title="Root", slug="root")
        home = root.add_child(instance=HomePage(title="Home", slug="ai-home"))
        self.site = Site.objects.create(
            hostname="testserver",
            root_page=home,
            is_default_site=True,
        )
        Site.clear_site_root_paths_cache()
        self.addCleanup(Site.clear_site_root_paths_cache)

        magazine = home.add_child(
            instance=MagazineIndexPage(title="Magazine", slug="magazine"),
        )
        department_index = magazine.add_child(
            instance=MagazineDepartmentIndexPage(title="Departments"),
        )
        department = department_index.add_child(
            instance=MagazineDepartment(title="Department"),
        )
        self.issue = magazine.add_child(
            instance=MagazineIssue(title="Issue", slug="issue"),
        )
        self.excluded = self.issue.add_child(
            instance=MagazineArticle(
                title="Excluded",
                slug="excluded",
                department=department,
                exclude_from_ai=True,
            ),
        )
        self.included = self.issue.add_child(
            instance=MagazineArticle(
                title="Included",
                slug="included",
                department=department,
            ),
        )

    def get_robots_groups(self):
        return robots_groups(self.client.get("/robots.txt").content.decode())

    def test_robots_txt_asks_all_crawlers_not_to_use_excluded_article_for_ai(self):
        everyone = self.get_robots_groups()["*"]

        self.assertIn(
            f"Content-Usage: {EXCLUDED_PATH} train-ai=n, ai-use=n, search=y",
            everyone,
        )
        self.assertNotIn(f"Disallow: {EXCLUDED_PATH}", everyone)
        self.assertNotIn(INCLUDED_PATH, "\n".join(everyone))

    def test_robots_txt_disallows_excluded_article_for_ai_crawlers(self):
        groups = self.get_robots_groups()
        ai_crawlers = groups[AI_CRAWLER_USER_AGENTS[0]]

        for agent in AI_CRAWLER_USER_AGENTS:
            self.assertIn(f"User-agent: {agent}", ai_crawlers)
        self.assertNotIn("User-agent: Googlebot", ai_crawlers)
        self.assertIn(f"Disallow: {EXCLUDED_PATH}", ai_crawlers)
        self.assertNotIn(f"Disallow: {INCLUDED_PATH}", ai_crawlers)

    def test_robots_txt_ai_crawler_group_keeps_site_wide_rules(self):
        groups = self.get_robots_groups()
        ai_crawlers = groups[AI_CRAWLER_USER_AGENTS[0]]

        self.assertIn(groups["*"][1], ai_crawlers)  # Content-Signal
        self.assertIn("Disallow: /admin/", ai_crawlers)

    def test_robots_txt_has_no_ai_crawler_group_without_exclusions(self):
        self.excluded.exclude_from_ai = False
        self.excluded.save_revision().publish()

        content = self.client.get("/robots.txt").content.decode()

        self.assertEqual(list(robots_groups(content)), ["*"])
        self.assertNotIn("Content-Usage", content)

    def test_robots_txt_skips_unpublished_articles(self):
        self.excluded.unpublish()

        self.assertNotIn(EXCLUDED_PATH, self.client.get("/robots.txt").content.decode())

    def test_exclusion_follows_article_when_slug_changes(self):
        self.excluded.slug = "renamed"
        self.excluded.save_revision().publish()

        content = self.client.get("/robots.txt").content.decode()

        self.assertNotIn(EXCLUDED_PATH, content)
        self.assertIn("Disallow: /magazine/issue/renamed/", content)
        response = self.client.get("/magazine/issue/renamed/")
        self.assertEqual(
            response["Content-Usage"],
            "train-ai=n, ai-use=n, search=y",
        )

    def test_llms_txt_skips_excluded_articles(self):
        NavigationMenuSetting.objects.create(
            site=self.site,
            menu_items=[
                ("internal_page", {"title": "Excluded essay", "page": self.excluded}),
                ("internal_page", {"title": "Included essay", "page": self.included}),
            ],
        )

        content = self.client.get("/llms.txt").content.decode()

        self.assertNotIn("Excluded essay", content)
        self.assertIn(f"[Included essay](http://testserver{INCLUDED_PATH})", content)

    def test_excluded_article_page_carries_content_usage_header(self):
        response = self.client.get(EXCLUDED_PATH)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response["Content-Usage"],
            "train-ai=n, ai-use=n, search=y",
        )

    def test_included_article_page_has_no_content_usage_header(self):
        response = self.client.get(INCLUDED_PATH)

        self.assertEqual(response.status_code, 200)
        self.assertNotIn("Content-Usage", response)

    def test_exclusion_is_editable_in_admin(self):
        admin = User.objects.create_superuser(email="admin@example.com", password=None)
        self.client.force_login(admin)

        response = self.client.get(
            reverse("wagtailadmin_pages:edit", args=[self.included.id]),
        )

        self.assertContains(response, 'name="exclude_from_ai"')
        self.assertContains(response, "Exclude from AI use")

    @patch("magazine.signals.PurgeBatch")
    def test_publishing_article_purges_robots_and_llms_txt(self, purge_batch):
        with self.captureOnCommitCallbacks(execute=True):
            self.included.save_revision().publish()

        purged = list(purge_batch.return_value.add_urls.call_args.args[0])
        self.assertEqual(
            purged,
            ["http://testserver/robots.txt", "http://testserver/llms.txt"],
        )
        purge_batch.return_value.purge.assert_called_once()
