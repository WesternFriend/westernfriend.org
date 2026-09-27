"""Tests for excluding individual magazine articles from AI use."""

from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse
from wagtail.models import Locale, Page, Site

from accounts.models import User
from common.models import CrawlerPolicySetting
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
EXCLUDED_USAGE = "train-ai=n, ai-use=n, search=y"
INCLUDED_PATH = "/magazine/issue/included/"


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

    def get_robots_txt(self):
        return self.client.get("/robots.txt").content.decode()

    def test_robots_txt_asks_crawlers_not_to_use_excluded_article_for_ai(self):
        content = self.get_robots_txt()

        self.assertIn(f"Content-Usage: {EXCLUDED_PATH} {EXCLUDED_USAGE}\n", content)
        self.assertNotIn(f"Disallow: {EXCLUDED_PATH}", content)
        self.assertNotIn(INCLUDED_PATH, content)

    def test_robots_txt_has_one_group(self):
        self.assertEqual(self.get_robots_txt().count("User-agent:"), 1)

    def test_excluded_article_follows_site_search_setting(self):
        CrawlerPolicySetting.objects.create(site=self.site, allow_search=False)
        usage = "train-ai=n, ai-use=n, search=n"

        self.assertIn(
            f"Content-Usage: {EXCLUDED_PATH} {usage}\n",
            self.get_robots_txt(),
        )
        self.assertEqual(self.client.get(EXCLUDED_PATH)["Content-Usage"], usage)

    def test_robots_txt_has_no_content_usage_without_exclusions(self):
        self.excluded.exclude_from_ai = False
        self.excluded.save_revision().publish()

        self.assertNotIn("Content-Usage", self.get_robots_txt())

    def test_robots_txt_skips_unpublished_articles(self):
        self.excluded.unpublish()

        self.assertNotIn(EXCLUDED_PATH, self.get_robots_txt())

    def test_exclusion_follows_article_when_slug_changes(self):
        self.excluded.slug = "renamed"
        self.excluded.save_revision().publish()

        content = self.get_robots_txt()

        self.assertNotIn(EXCLUDED_PATH, content)
        self.assertIn("Content-Usage: /magazine/issue/renamed/ ", content)
        response = self.client.get("/magazine/issue/renamed/")
        self.assertEqual(response["Content-Usage"], EXCLUDED_USAGE)

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
        self.assertIn(f"[Included essay](<http://testserver{INCLUDED_PATH}>)", content)

    def test_excluded_article_page_carries_content_usage_header(self):
        response = self.client.get(EXCLUDED_PATH)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Usage"], EXCLUDED_USAGE)

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

    def test_robots_txt_percent_encodes_unicode_slugs_once(self):
        self.excluded.slug = "café"
        self.excluded.save_revision().publish()

        content = self.get_robots_txt()

        self.assertIn("Content-Usage: /magazine/issue/caf%C3%A9/ ", content)
        self.assertNotIn("%25", content)

    @patch("magazine.signals.PurgeBatch")
    def test_publishing_issue_with_excluded_article_purges(self, purge_batch):
        self.issue.slug = "renamed-issue"
        with self.captureOnCommitCallbacks(execute=True):
            self.issue.save_revision().publish()

        purge_batch.return_value.purge.assert_called_once()

    @patch("magazine.signals.PurgeBatch")
    def test_publishing_unrelated_page_does_not_purge(self, purge_batch):
        self.excluded.exclude_from_ai = False
        self.excluded.save_revision().publish()
        purge_batch.reset_mock()

        with self.captureOnCommitCallbacks(execute=True):
            self.issue.save_revision().publish()

        purge_batch.return_value.purge.assert_not_called()
