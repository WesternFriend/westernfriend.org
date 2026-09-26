"""Tests for core utility functions."""

from django.test import TestCase
from wagtail.models import Locale, Page, PageViewRestriction, Site

from core.utils import get_default_site
from navigation.models import NavigationMenuSetting


class GetDefaultSiteTest(TestCase):
    """Test the get_default_site utility function."""

    def setUp(self):
        """Set up test data."""
        # Create locale if needed
        Locale.objects.get_or_create(language_code="en")

        # Create a root page
        try:
            self.root = Page.objects.get(depth=1)
        except Page.DoesNotExist:
            self.root = Page.add_root(title="Root", slug="root")

    def test_returns_default_site(self):
        """Test that function returns the default site when one exists."""
        site = Site.objects.create(
            hostname="example.com",
            root_page=self.root,
            is_default_site=True,
        )

        result = get_default_site()
        self.assertEqual(result, site)

    def test_returns_first_site_when_no_default(self):
        """Test that function returns first site when no default exists."""
        # Clear all sites first
        Site.objects.all().delete()

        site = Site.objects.create(
            hostname="example.com",
            root_page=self.root,
            is_default_site=False,
        )

        result = get_default_site()
        self.assertEqual(result, site)

    def test_returns_none_when_no_sites_exist(self):
        """Test that function returns None when no sites exist."""
        # Ensure no sites exist
        Site.objects.all().delete()

        result = get_default_site()
        self.assertIsNone(result)

    def test_handles_multiple_default_sites_gracefully(self):
        """Test that function handles edge case of multiple default sites.

        This can happen in test environments where multiple test cases
        create default sites.
        """
        site1 = Site.objects.create(
            hostname="example1.com",
            root_page=self.root,
            is_default_site=True,
        )
        Site.objects.create(
            hostname="example2.com",
            root_page=self.root,
            is_default_site=True,
        )

        # Should return the first default site without raising an exception
        result = get_default_site()
        self.assertIsNotNone(result)
        self.assertEqual(result, site1)


class RobotsTxtTest(TestCase):
    """Test the robots.txt view."""

    def test_robots_txt_references_canonical_sitemap(self):
        response = self.client.get("/robots.txt")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/plain")
        self.assertIn(
            "Sitemap: https://westernfriend.org/sitemap.xml",
            response.content.decode(),
        )

    def test_robots_txt_disallows_admin(self):
        response = self.client.get("/robots.txt")

        self.assertIn("Disallow: /admin/", response.content.decode())

    def test_robots_txt_disallows_search(self):
        response = self.client.get("/robots.txt")

        self.assertIn("Disallow: /search/", response.content.decode())

    def test_robots_txt_allows_search_and_ai_use(self):
        response = self.client.get("/robots.txt")

        self.assertIn(
            "Content-Signal: search=yes, ai-input=yes, ai-train=yes",
            response.content.decode(),
        )


class SitemapTest(TestCase):
    """Test the sitemap.xml view."""

    def setUp(self):
        Locale.objects.get_or_create(language_code="en")
        Site.objects.all().delete()
        root = Page.get_first_root_node() or Page.add_root(title="Root", slug="root")
        self.home = root.add_child(instance=Page(title="Home", slug="sitemap-home"))
        Site.objects.create(
            hostname="testserver",
            root_page=self.home,
            is_default_site=True,
        )
        Site.clear_site_root_paths_cache()
        self.addCleanup(Site.clear_site_root_paths_cache)
        self.child = self.home.add_child(instance=Page(title="About", slug="about"))

    def test_sitemap_is_xml(self):
        response = self.client.get("/sitemap.xml")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/xml")
        self.assertIn(
            b'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"',
            response.content,
        )

    def test_sitemap_lists_published_pages(self):
        response = self.client.get("/sitemap.xml")

        self.assertIn(b"<loc>http://testserver/about/</loc>", response.content)

    def test_sitemap_excludes_unpublished_pages(self):
        self.child.unpublish()

        response = self.client.get("/sitemap.xml")

        self.assertNotIn(b"/about/", response.content)


class LlmsTxtTest(TestCase):
    """Test the llms.txt view."""

    def setUp(self):
        Locale.objects.get_or_create(language_code="en")
        Site.objects.all().delete()
        root = Page.get_first_root_node() or Page.add_root(title="Root", slug="root")
        home = root.add_child(instance=Page(title="Home", slug="llms-home"))
        site = Site.objects.create(
            hostname="testserver",
            root_page=home,
            is_default_site=True,
        )
        Site.clear_site_root_paths_cache()
        self.addCleanup(Site.clear_site_root_paths_cache)
        magazine = home.add_child(
            instance=Page(
                title="Magazine",
                slug="magazine",
                search_description="Quaker writing and art",
            ),
        )
        draft = home.add_child(instance=Page(title="Draft", slug="draft"))
        draft.unpublish()
        members = home.add_child(instance=Page(title="Members", slug="members"))
        PageViewRestriction.objects.create(
            page=members,
            restriction_type=PageViewRestriction.LOGIN,
        )
        about = home.add_child(instance=Page(title="About", slug="about"))
        NavigationMenuSetting.objects.create(
            site=site,
            menu_items=[
                (
                    "drop_down",
                    {
                        "title": "Read",
                        "menu_items": [
                            ("page", {"title": "Current issue", "page": magazine}),
                            ("page", {"title": "Coming soon", "page": draft}),
                            ("page", {"title": "Members only", "page": members}),
                            (
                                "external_link",
                                {"title": "Podcast", "url": "https://example.com/pod"},
                            ),
                        ],
                    },
                ),
                ("internal_page", {"title": "About us", "page": about}),
            ],
        )

    def test_llms_txt_is_markdown_with_title(self):
        response = self.client.get("/llms.txt")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/plain; charset=utf-8")
        self.assertTrue(response.content.decode().startswith("# Western Friend\n"))

    def test_llms_txt_lists_navigation_menu(self):
        content = self.client.get("/llms.txt").content.decode()

        self.assertIn("## Pages\n\n- [About us](http://testserver/about/)\n", content)
        self.assertIn(
            "## Read\n\n"
            "- [Current issue](http://testserver/magazine/): Quaker writing and art\n"
            "- [Podcast](https://example.com/pod)\n",
            content,
        )

    def test_llms_txt_skips_unpublished_pages(self):
        content = self.client.get("/llms.txt").content.decode()

        self.assertNotIn("Coming soon", content)

    def test_llms_txt_skips_restricted_pages(self):
        content = self.client.get("/llms.txt").content.decode()

        self.assertNotIn("Members only", content)

    def test_llms_txt_links_sitemap(self):
        content = self.client.get("/llms.txt").content.decode()

        self.assertIn("(https://westernfriend.org/sitemap.xml)", content)


class DiscoveryLinkHeaderTest(TestCase):
    """Test the Link header that points agents at llms.txt and the sitemap."""

    def test_html_pages_link_llms_txt_and_sitemap(self):
        response = self.client.get("/no-such-page/")

        self.assertTrue(response["Content-Type"].startswith("text/html"))
        self.assertEqual(
            response["Link"],
            '</llms.txt>; rel="describedby"; type="text/plain", '
            '</sitemap.xml>; rel="sitemap"; type="application/xml"',
        )

    def test_non_html_responses_have_no_link_header(self):
        response = self.client.get("/robots.txt")

        self.assertNotIn("Link", response)
