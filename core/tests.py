"""Tests for core utility functions."""

from django.test import TestCase
from wagtail.models import Locale, Page, Site

from core.utils import get_default_site


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
