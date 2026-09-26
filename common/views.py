from http import HTTPStatus
from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.http import require_GET
from wagtail.admin.viewsets.base import ViewSetGroup

from community.views import CommunityDirectoryViewSet, OnlineWorshipViewSet
from documents.views import MeetingDocumentViewSet, PublicBoardDocumentViewSet
from events.views import EventViewSet
from navigation.models import NavigationMenuSetting
from news.views import NewsItemViewSet
from tags.views import TagViewSet
from wf_pages.views import MollyWingateBlogPageViewSet


class ContentViewSetGroup(ViewSetGroup):
    menu_label = "Content"
    menu_icon = "snippet"
    menu_order = 101
    items = [
        CommunityDirectoryViewSet,
        EventViewSet,
        NewsItemViewSet,
        OnlineWorshipViewSet,
        MeetingDocumentViewSet,
        PublicBoardDocumentViewSet,
        MollyWingateBlogPageViewSet,
        TagViewSet,
    ]


def custom_404(request, exception=None):  # noqa: W0613 # skipcq: PYL-W0613
    """Return the 404 page with search form that will contain the URL path
    components that the user requested. The path will be split into the
    keywords and the keywords will be used to populate the search field.

    E.g., westernfriend.org/some-missing-page/with-subpage will return
    the 404 page with the search field populated with "some missing page
    with subpage".
    """
    context = {}

    # Get the path from the request
    path = request.path

    # Split the requested path to form a search query
    # e.g. /page-not-found/ -> page not found
    search_query = path.replace("-", " ").replace("/", " ").strip()

    # Add the custom variable to the context dictionary
    context["search_query"] = search_query

    # Render the 404 page with the custom variable
    return render(
        request,
        "404.html",
        context=context,
        status=HTTPStatus.NOT_FOUND,
    )


# Private or transactional paths that crawlers should not index
ROBOTS_DISALLOWED_PATHS = [
    "/admin/",
    "/accounts/",
    "/cart/",
    "/orders/",
    "/payment/",
    "/paypal/",
]


# We want Quaker perspectives to be available to search engines, AI answers,
# and AI training alike (https://contentsignals.org/)
ROBOTS_CONTENT_SIGNAL = "search=yes, ai-input=yes, ai-train=yes"


def _absolute_url(path):
    return f"{settings.BASE_URL.rstrip('/')}{path}"


@require_GET
def robots_txt(request):
    """Serve robots.txt, pointing crawlers at the canonical sitemap."""
    lines = ["User-agent: *", f"Content-Signal: {ROBOTS_CONTENT_SIGNAL}"]
    lines += [f"Disallow: {path}" for path in ROBOTS_DISALLOWED_PATHS]
    lines += ["", f"Sitemap: {_absolute_url(reverse('sitemap'))}", ""]

    return HttpResponse("\n".join(lines), content_type="text/plain")


def _llms_link(request, item):
    """Format a navigation menu link as an llms.txt list item."""
    page = item.get("page")
    if page is not None and (not page.live or page.get_view_restrictions().exists()):
        return None

    line = f"- [{item['title']}]({request.build_absolute_uri(item.href())})"
    description = page.specific.search_description if page is not None else ""
    return f"{line}: {description}" if description else line


@require_GET
def llms_txt(request):
    """Serve llms.txt (https://llmstxt.org/), built from the navigation menu."""
    lines = [
        "# Western Friend",
        "",
        (
            "> Western Friend is a Quaker nonprofit that publishes a magazine, "
            "books, and other resources exploring the spiritual lives of Friends "
            "(Quakers) in the western United States and beyond."
        ),
        "",
    ]

    top_level_links = []
    sections = []
    for block in NavigationMenuSetting.for_request(request).menu_items:
        if block.block_type == "drop_down":
            links = [
                _llms_link(request, child.value) for child in block.value["menu_items"]
            ]
            sections.append((block.value["title"], links))
        else:
            top_level_links.append(_llms_link(request, block.value))
    if top_level_links:
        sections.insert(0, ("Pages", top_level_links))

    for title, links in sections:
        links = [link for link in links if link]
        if links:
            lines += [f"## {title}", "", *links, ""]

    lines += [
        "## Optional",
        "",
        f"- [Sitemap]({_absolute_url(reverse('sitemap'))}): every public page",
        "",
    ]

    return HttpResponse("\n".join(lines), content_type="text/plain; charset=utf-8")
