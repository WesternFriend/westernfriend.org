from wagtail.core import blocks
from wagtail.core.blocks import StructValue


class NavigationExternalLinkStructValue(StructValue):
    def href(self):
        """Construct a URL with anchor if exists, otherwise use URL"""
        url = self.get("url")
        anchor = self.get("anchor")

        href = f"{ url }#{ anchor }" if anchor else url

        return href


class NavigationExternalLinkBlock(blocks.StructBlock):
    title = blocks.CharBlock()
    url = blocks.URLBlock()
    anchor = blocks.CharBlock(
        required=False,
        help_text="For linking to specific page elements. Enter the anchor text without the leading '#' symbol."
    )

    class Meta:
        template = "navigation/blocks/nav_link.html"
        label = "External link"
        icon = "link-external"
        value_class = NavigationExternalLinkStructValue


class NavigationPageChooserStructValue(StructValue):
    def href(self):
        """Construct a URL with anchor if exists, otherwise use URL"""
        url = self.get("page").url
        anchor = self.get("anchor")

        href = f"{ url }#{ anchor }" if anchor else url

        return href


class NavigationPageChooserBlock(blocks.StructBlock):
    title = blocks.CharBlock()
    page = blocks.PageChooserBlock()
    anchor = blocks.CharBlock(
        required=False,
        help_text="For linking to specific page elements. Enter the anchor text without the leading '#' symbol."
    )

    class Meta:
        template = "navigation/blocks/nav_link.html"
        label = "Internal page link"
        icon = "doc-empty"
        value_class = NavigationPageChooserStructValue


class NavigationDropdownMenuBlock(blocks.StructBlock):
    title = blocks.CharBlock()
    items = blocks.StreamBlock([
        ("page", NavigationPageChooserBlock()),
        ("external_link", NavigationExternalLinkBlock()),
    ])

    class Meta:
        template = "navigation/blocks/dropdown_menu.html"
        label = "Dropdown menu"
        icon = "arrow-down-big"
