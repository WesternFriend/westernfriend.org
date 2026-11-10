from html.parser import HTMLParser

from wagtail.models import Page


class LinkTargets(HTMLParser):
    """Collect where every link in a page goes."""

    def __init__(self) -> None:
        super().__init__()
        self.hrefs: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "a":
            self.hrefs.extend(
                value for name, value in attrs if name == "href" and value
            )


def link_targets(html: str) -> list[str]:
    """Return the href of every link in the HTML, in page order."""
    parser = LinkTargets()
    parser.feed(html)
    return parser.hrefs


def links_missing_slash(hrefs: list[str], path: str) -> list[str]:
    """Return the links to path that leave off its trailing slash.

    "/cart", "/cart?step=2" and "/cart#items" all reach "/cart/" only through
    Django's APPEND_SLASH redirect.
    """
    return [
        href
        for href in hrefs
        if href == path or href.startswith((f"{path}?", f"{path}#"))
    ]


def get_or_create_site_root_page() -> Page:
    root_page: Page
    try:
        root_page = Page.objects.get(
            id=1,
        )
    except Page.DoesNotExist:
        root_page = Page.objects.create(
            id=1,
        ).save()

    return root_page
