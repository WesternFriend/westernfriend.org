import hashlib
from http import HTTPStatus
from urllib.parse import quote, unquote

from django.conf import settings
from django.core.cache import cache
from django.db.models import Max
from django.http import Http404, HttpResponse, HttpResponsePermanentRedirect
from django.shortcuts import render
from django.templatetags.static import static
from django.urls import reverse
from django.views.decorators.http import require_GET
from wagtail.admin.viewsets.base import ViewSetGroup
from wagtail.contrib.sitemaps.views import sitemap as wagtail_sitemap
from wagtail.models import PageLogEntry, Site

from common.models import CrawlerPolicySetting
from community.views import CommunityDirectoryViewSet, OnlineWorshipViewSet
from documents.views import MeetingDocumentViewSet, PublicBoardDocumentViewSet
from events.views import EventViewSet
from magazine.models import MagazineArticle
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


def custom_404(request, exception=None):  # skipcq: PYL-W0613
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


# Private, transactional, or costly paths that crawlers should not index.
# These stay in code, whatever the crawler policy setting says.
ROBOTS_DISALLOWED_PATHS = [
    "/admin/",
    "/accounts/",
    "/cart/",
    "/orders/",
    "/payment/",
    "/paypal/",
    "/search/",
]


def _absolute_url(path):
    return f"{settings.BASE_URL.rstrip('/')}{path}"


@require_GET
def favicon_ico(request):
    """Redirect browsers' automatic /favicon.ico requests to the static icon."""
    return HttpResponsePermanentRedirect(static("img/favicon.ico"))


def _ai_excluded_paths(request):
    """Return the URL paths of live articles excluded from AI use on this site.

    Paths are looked up on every request, so an exclusion follows the
    article when its slug or parent changes.
    """
    site = Site.find_for_request(request)
    paths = []
    for article in MagazineArticle.objects.live().filter(exclude_from_ai=True):
        url_parts = article.get_url_parts(request)
        if url_parts is not None and url_parts[0] == getattr(site, "id", None):
            # Normalise to one level of percent-encoding, whether or not
            # Wagtail has already encoded a Unicode slug
            paths.append(quote(unquote(url_parts[2]), safe="/"))
    return sorted(paths)


@require_GET
def robots_txt(request):
    """Serve robots.txt, pointing crawlers at the canonical sitemap.

    Articles excluded from AI use get a path-scoped Content-Usage rule.
    See docs/ai-opt-out.md.
    """
    policy = CrawlerPolicySetting.for_request_or_default(request)
    excluded_paths = _ai_excluded_paths(request)

    lines = ["User-agent: *", f"Content-Signal: {policy.content_signal}"]
    lines += [
        f"Content-Usage: {path} {policy.excluded_content_usage}"
        for path in excluded_paths
    ]
    lines += [f"Disallow: {path}" for path in ROBOTS_DISALLOWED_PATHS]

    lines += ["", f"Sitemap: {_absolute_url(reverse('sitemap'))}", ""]

    return HttpResponse("\n".join(lines), content_type="text/plain")


def _llms_link(request, item):
    """Format a navigation menu link as an llms.txt list item.

    The destination is wrapped in angle brackets (allowed by CommonMark) so
    URLs containing an unmatched ")" or a space can't truncate the link.
    """
    page = item.get("page")
    if page is not None and (
        not page.live
        or page.get_view_restrictions().exists()
        or getattr(page.specific, "exclude_from_ai", False)
    ):
        return None

    line = f"- [{item['title']}](<{request.build_absolute_uri(item.href())}>)"
    description = page.specific.search_description if page is not None else ""
    return f"{line}: {description}" if description else line


@require_GET
def llms_txt(request):
    """Serve llms.txt (https://llmstxt.org/), built from the navigation menu."""
    policy = CrawlerPolicySetting.for_request_or_default(request)
    if not policy.publish_llms_txt:
        raise Http404

    lines = ["# Western Friend", ""]
    summary = " ".join(policy.llms_txt_summary.split())
    if summary:
        lines += [f"> {summary}", ""]

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

    for title, section_links in sections:
        links = [link for link in section_links if link]
        if links:
            lines += [f"## {title}", "", *links, ""]

    lines += [
        "## Optional",
        "",
        f"- [Sitemap](<{_absolute_url(reverse('sitemap'))}>): every public page",
        "",
    ]

    return HttpResponse("\n".join(lines), content_type="text/plain; charset=utf-8")


# Audit log actions that can add, remove, or move a page in the sitemap
SITEMAP_CHANGE_ACTIONS = [
    "wagtail.copy",
    "wagtail.delete",
    "wagtail.move",
    "wagtail.publish",
    "wagtail.publish.scheduled",
    "wagtail.unpublish",
    "wagtail.unpublish.scheduled",
    "wagtail.view_restriction.create",
    "wagtail.view_restriction.delete",
    "wagtail.view_restriction.edit",
]

# A safety net; the cache key changes whenever a page is published or removed
SITEMAP_CACHE_SECONDS = 60 * 60 * 24


@require_GET
def sitemap(request):
    """Serve Wagtail's sitemap, cached until the next page change.

    The sitemap lists every page and takes seconds to build, which is longer
    than some crawlers wait. Keying the cache on the latest audit log entry
    and the site settings keeps every worker's copy current without a shared
    cache backend.
    """
    last_change = PageLogEntry.objects.filter(
        action__in=SITEMAP_CHANGE_ACTIONS,
    ).aggregate(Max("timestamp"))["timestamp__max"]
    # Site hostnames and root pages decide every URL in the sitemap. Wagtail
    # caches these, so including them costs no query.
    sites = hashlib.sha256(repr(Site.get_site_root_paths()).encode()).hexdigest()
    cache_key = "sitemap:{}:{}:{}".format(
        request.get_host(),
        sites[:16],
        last_change.isoformat() if last_change else "never",
    )

    content = cache.get(cache_key)
    if content is None:
        response = wagtail_sitemap(request)
        response.render()
        content = response.content
        cache.set(cache_key, content, SITEMAP_CACHE_SECONDS)

    return HttpResponse(content, content_type="application/xml")
