from wagtail import blocks as wagtail_blocks
from wagtail.blocks import StructValue


class NavigationLinkBlock(wagtail_blocks.StructBlock):
    """Render a link with an href resolved against the current request."""

    def get_context(self, value, parent_context=None):
        context = super().get_context(value, parent_context=parent_context)
        request = (parent_context or {}).get("request")
        context["href"] = value.href(request=request)
        return context


class NavigationExternalLinkStructValue(StructValue):
    def href(self, request=None) -> str:
        """Construct a URL with anchor if exists, otherwise use URL."""
        url = self.get("url")
        anchor = self.get("anchor")

        if url and anchor:
            return f"{url}#{anchor}"
        if url:
            return url
        if anchor:
            return f"#{anchor}"
        return ""


class NavigationExternalLinkBlock(NavigationLinkBlock):
    title = wagtail_blocks.CharBlock()
    url = wagtail_blocks.URLBlock()
    anchor = wagtail_blocks.CharBlock(
        required=False,
        help_text="For linking to specific page elements. Enter the anchor text without the leading '#' symbol.",
    )

    class Meta:
        template = "navigation/blocks/nav_link.html"
        label = "External link"
        icon = "link-external"
        value_class = NavigationExternalLinkStructValue


class NavigationPageChooserStructValue(StructValue):
    def href(self, request=None):
        """Construct a URL with anchor if exists, otherwise use URL.

        Pass the request so the page URL reuses the site root paths cached on
        it; without one, each menu page does its own cache lookup.
        """
        page = self.get("page")
        url = "#" if page is None else page.get_url(request=request)
        anchor = self.get("anchor")

        if url and anchor:
            return f"{url}#{anchor}"
        if url:
            return url
        if anchor:
            return f"#{anchor}"
        return "#"


class NavigationPageChooserBlock(NavigationLinkBlock):
    title = wagtail_blocks.CharBlock()
    page = wagtail_blocks.PageChooserBlock()
    anchor = wagtail_blocks.CharBlock(
        required=False,
        help_text="For linking to specific page elements. Enter the anchor text without the leading '#' symbol.",
    )

    class Meta:
        template = "navigation/blocks/nav_link.html"
        label = "Internal page link"
        icon = "doc-empty"
        value_class = NavigationPageChooserStructValue


class NavigationDropdownMenuStructValue(StructValue):
    def submenu_id(self):
        """Generate a unique ID for the submenu based on the title.

        This is used for accessibility purposes to link the summary and menu elements.
        """
        # Create a slug-like string from the title that can be used as an HTML id
        title = self.get("title", "")
        # Convert to lowercase and replace spaces with hyphens
        base_id = title.lower().replace(" ", "-")
        # Only keep alphanumeric characters and hyphens
        clean_id = "".join(c for c in base_id if c.isalnum() or c == "-")
        return f"dropdown-menu-{clean_id}"


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
        value_class = NavigationDropdownMenuStructValue
