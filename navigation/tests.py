from django.test import TestCase
from wagtail.models import Site

from home.models import HomePage

from .blocks import (
    NavigationPageChooserBlock,
    NavigationExternalLinkBlock,
    NavigationExternalLinkStructValue,
)


class TestNavigationExternalLinkStructValue(TestCase):
    def test_href_with_anchor(self) -> None:
        # Create a NavigationExternalLinkStructValue object
        nav_struct_value = NavigationExternalLinkStructValue(
            NavigationExternalLinkBlock(),
            {
                "url": "http://example.com",
                "anchor": "myanchor",
            },
        )

        self.assertEqual(
            nav_struct_value.href(),
            "http://example.com#myanchor",
        )

    def test_href_without_anchor(self) -> None:
        nav_struct_value = NavigationExternalLinkStructValue(
            NavigationExternalLinkBlock(),
            {
                "url": "http://example.com",
                "anchor": None,
            },
        )

        self.assertEqual(
            nav_struct_value.href(),
            "http://example.com",
        )

    def test_href_with_no_url(self) -> None:
        nav_struct_value = NavigationExternalLinkStructValue(
            NavigationExternalLinkBlock(),
            {
                "url": None,
                "anchor": "myanchor",
            },
        )

        self.assertEqual(nav_struct_value.href(), "#myanchor")


class TestNavigationPageChooserStructValue(TestCase):
    def setUp(self) -> None:
        self.site = Site.objects.get(is_default_site=True)

        self.home_page = HomePage(
            title="Home",
        )

        self.site.root_page.add_child(instance=self.home_page)

    def test_href_with_anchor(self) -> None:
        # Instantiate the block
        block = NavigationPageChooserBlock()

        # Convert your data to a StructValue instance using the block
        block_value = block.to_python(
            {
                "title": "My page",
                "page": self.home_page.id,
                "anchor": "myanchor",
            },
        )

        self.assertEqual(
            block_value.href(),
            f"{self.home_page.url}#myanchor",
        )

    def test_href_without_anchor(self) -> None:
        # Instantiate the block
        block = NavigationPageChooserBlock()

        # Convert your data to a StructValue instance using the block
        block_value = block.to_python(
            {
                "title": "My page",
                "page": self.home_page.id,
                "anchor": None,
            },
        )

        # Now you can call methods on the StructValue instance
        self.assertEqual(
            block_value.href(),
            self.home_page.url,
        )
