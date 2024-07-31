from wagtail import blocks as wagtail_blocks
from wagtail.blocks import StructValue


class NavigationExternalLinkStructValue(StructValue):
    def href(self) -> str:
        """Construct a URL with anchor if exists, otherwise use URL."""
        url = self.get("url")
        anchor = self.get("anchor")

        if url and anchor:
            return f"{url}#{anchor}"
        elif url:
            return url
        elif anchor:
            return f"#{anchor}"
        else:
            return ""


class NavigationExternalLinkBlock(wagtail_blocks.StructBlock):
    title = wagtail_blocks.CharBlock()
    url = wagtail_blocks.URLBlock()
    anchor = wagtail_blocks.CharBlock(
        required=False,
        help_text="For linking to specific page elements. Enter the anchor text without the leading '#' symbol.",  # noqa: E501
    )

    class Meta:
        template = "navigation/blocks/nav_link.html"
        label = "External link"
        icon = "link-external"
        value_class = NavigationExternalLinkStructValue


class NavigationPageChooserStructValue(StructValue):
    def href(self):
        """Construct a URL with anchor if exists, otherwise use URL."""
        page = self.get("page")
        if page is None:
            url = "#"  # or some other default URL
        else:
            url = page.url
        anchor = self.get("anchor")

        if url and anchor:
            return f"{url}#{anchor}"
        elif url:
            return url
        elif anchor:
            return f"#{anchor}"
        else:
            return "#"


class NavigationPageChooserBlock(wagtail_blocks.StructBlock):
    title = wagtail_blocks.CharBlock()
    page = wagtail_blocks.PageChooserBlock()
    anchor = wagtail_blocks.CharBlock(
        required=False,
        help_text="For linking to specific page elements. Enter the anchor text without the leading '#' symbol.",  # noqa: E501
    )

    class Meta:
        template = "navigation/blocks/nav_link.html"
        label = "Internal page link"
        icon = "doc-empty"
        value_class = NavigationPageChooserStructValue


class NavigationDropdownMenuBlock(wagtail_blocks.StructBlock):
    title = wagtail_blocks.CharBlock()
    menu_items = wagtail_blocks.StreamBlock(
        [
            ("page", NavigationPageChooserBlock()),
            ("external_link", NavigationExternalLinkBlock()),
        ],
    )

    class Meta:
        template = "navigation/blocks/dropdown_menu.html"
        label = "Dropdown menu"
        icon = "arrow-down-big"
