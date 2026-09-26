from django.test import TestCase
from wagtail.models import Site

from home.models import HomePage

from .blocks import (
    NavigationDropdownMenuBlock,
    NavigationDropdownMenuStructValue,
    NavigationExternalLinkBlock,
    NavigationExternalLinkStructValue,
    NavigationPageChooserBlock,
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


class TestNavigationDropdownMenuStructValue(TestCase):
    def test_submenu_id_with_simple_title(self) -> None:
        """Test submenu_id generation with a simple title."""
        nav_struct_value = NavigationDropdownMenuStructValue(
            NavigationDropdownMenuBlock(),
            {
                "title": "About Us",
                "menu_items": [],
            },
        )

        self.assertEqual(
            nav_struct_value.submenu_id(),
            "dropdown-menu-about-us",
        )

    def test_submenu_id_with_special_characters(self) -> None:
        """Test submenu_id generation with special characters in the title."""
        nav_struct_value = NavigationDropdownMenuStructValue(
            NavigationDropdownMenuBlock(),
            {
                "title": "FAQ & Support!",
                "menu_items": [],
            },
        )

        self.assertEqual(
            nav_struct_value.submenu_id(),
            "dropdown-menu-faq--support",
        )

    def test_submenu_id_with_empty_title(self) -> None:
        """Test submenu_id generation with an empty title."""
        nav_struct_value = NavigationDropdownMenuStructValue(
            NavigationDropdownMenuBlock(),
            {
                "title": "",
                "menu_items": [],
            },
        )

        self.assertEqual(
            nav_struct_value.submenu_id(),
            "dropdown-menu-",
        )
