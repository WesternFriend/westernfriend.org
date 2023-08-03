from django.test import TestCase
from wagtail_factories import PageFactory

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
        # Create a test page
        self.test_page = PageFactory.create()

    def test_href_with_anchor(self) -> None:
        # Instantiate the block
        block = NavigationPageChooserBlock()

        # Convert your data to a StructValue instance using the block
        block_value = block.to_python(
            {
                "title": "My page",
                "page": self.test_page.id,
                "anchor": "myanchor",
            },
        )

        self.assertEqual(
            block_value.href(),
            f"{self.test_page.url}#myanchor",
        )

    def test_href_without_anchor(self) -> None:
        # Instantiate the block
        block = NavigationPageChooserBlock()

        # Convert your data to a StructValue instance using the block
        block_value = block.to_python(
            {
                "title": "My page",
                "page": self.test_page.id,
                "anchor": None,
            },
        )

        # Now you can call methods on the StructValue instance
        self.assertEqual(
            block_value.href(),
            self.test_page.url,
        )
