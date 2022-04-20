from wagtail.core import blocks


class NavigationExternalLinkBlock(blocks.StructBlock):
    title = blocks.CharBlock()
    url = blocks.URLBlock()

    class Meta:
        template = "navigation/blocks/external_link.html"
        label = "External link"
        icon = "link-external"


class NavigationPageChooserBlock(blocks.StructBlock):
    title = blocks.CharBlock()
    page = blocks.PageChooserBlock()

    class Meta:
        template = "navigation/blocks/page_link.html"
        label = "Internal page link"
        icon = "doc-empty"


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
