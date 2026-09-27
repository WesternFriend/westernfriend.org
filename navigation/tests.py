from unittest.mock import Mock

from django.test import SimpleTestCase, TestCase
from django.urls import reverse
from wagtail.models import Site

from home.models import HomePage

from .blocks import (
    NavigationDropdownMenuBlock,
    NavigationDropdownMenuStructValue,
    NavigationExternalLinkBlock,
    NavigationExternalLinkStructValue,
    NavigationPageChooserBlock,
    NavigationPageChooserStructValue,
)
from .models import NavigationMenuSetting


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

    def test_href_with_no_url_or_anchor(self) -> None:
        nav_struct_value = NavigationExternalLinkStructValue(
            NavigationExternalLinkBlock(),
            {
                "url": None,
                "anchor": None,
            },
        )

        self.assertEqual(nav_struct_value.href(), "")


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


class TestNavigationPageChooserStructValueWithoutPageUrl(SimpleTestCase):
    """A page with no URL (e.g. not routable from any site) falls back to anchors."""

    def make_value(self, anchor):
        return NavigationPageChooserStructValue(
            NavigationPageChooserBlock(),
            {"title": "My page", "page": Mock(url=None), "anchor": anchor},
        )

    def test_href_with_anchor_only(self) -> None:
        self.assertEqual(self.make_value("myanchor").href(), "#myanchor")

    def test_href_with_neither(self) -> None:
        self.assertEqual(self.make_value(None).href(), "#")


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


class TestNavigationMenuRendering(TestCase):
    """The navbar must render menu items as a valid list of links."""

    def setUp(self) -> None:
        self.site = Site.objects.get(is_default_site=True)
        NavigationMenuSetting.objects.update_or_create(
            site=self.site,
            defaults={
                "menu_items": [
                    (
                        "external_link",
                        {
                            "title": "Quaker Links",
                            "url": "https://example.com",
                            "anchor": "",
                        },
                    ),
                    (
                        "drop_down",
                        {
                            "title": "About Us",
                            "menu_items": [
                                (
                                    "external_link",
                                    {
                                        "title": "History",
                                        "url": "https://example.com/h",
                                        "anchor": "",
                                    },
                                ),
                            ],
                        },
                    ),
                ],
            },
        )

    def test_menu_items_render_as_list_items_without_menu_roles(self) -> None:
        html = self.client.get(reverse("login")).content.decode()

        links = html.split(
            'class="menu menu-horizontal menu-compact bg-black website-links"',
            1,
        )[1]
        links = links.split("</ul>\n", 1)[0]
        # include_block renders each <li> directly, without StreamField wrapper divs
        self.assertNotIn("<div", links.split("<details>", 1)[0])
        self.assertIn("Quaker Links", links)
        self.assertIn("<summary", links)
        self.assertNotIn('role="menu', html)
