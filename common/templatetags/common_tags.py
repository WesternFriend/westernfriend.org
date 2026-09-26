import json

from django import template
from django.core.serializers.json import DjangoJSONEncoder
from django.templatetags.static import static
from django.utils.safestring import SafeString, mark_safe
from wagtail.models import Site

register = template.Library()

# Matches Django's json_script escaping so values can't close the <script> element.
_JSON_SCRIPT_ESCAPES = {
    ord(">"): "\\u003E",
    ord("<"): "\\u003C",
    ord("&"): "\\u0026",
}


@register.filter
def json_ld(value) -> SafeString:
    """Serialize a value as JSON safe for embedding in a <script> element."""
    json_str = json.dumps(value, cls=DjangoJSONEncoder)
    return mark_safe(json_str.translate(_JSON_SCRIPT_ESCAPES))


@register.simple_tag(takes_context=True)
def absolute_static(context, path):
    """Return a fully qualified URL for a static file.

    Structured data needs absolute URLs, and STATIC_URL is relative
    unless static files are served from a CDN such as Spaces.
    """
    url = static(path)
    request = context.get("request")
    return request.build_absolute_uri(url) if request else url


@register.simple_tag(takes_context=True)
def site_root_url(context):
    """Return the absolute URL of the current Wagtail site's home page."""
    request = context.get("request")
    if request is None:
        return ""
    site = Site.find_for_request(request)
    return f"{site.root_url}/" if site else request.build_absolute_uri("/")


@register.simple_tag(takes_context=True)
def canonical_url(context):
    """Return the absolute canonical URL for the current page or request.

    Wagtail pages use their site's hostname, so www and bare-domain
    requests share one canonical URL.
    """
    request = context.get("request")
    page = context.get("page")
    if page is not None and hasattr(page, "get_full_url"):
        url = page.get_full_url(request)
        if url:
            return url
    return request.build_absolute_uri(request.path) if request else ""


@register.filter
def model_name(value):
    """Return the model name of the given object."""

    if value and hasattr(value, "_meta"):
        return value._meta.model_name
    return ""


EXCLUDED_BREADCRUMB_MODELS = [
    "homepage",
    "personindexpage",
    "meetingindexpage",
    "organizationindexpage",
    "facetindexpage",
    "audienceindexpage",
    "genreindexpage",
    "mediumindexpage",
    "timeperiodindexpage",
    "topicindexpage",
    "productindexpage",
]


@register.filter
def specific_pages(queryset):
    """Return ancestors as their specific page types, fetched in bulk.

    Replaces per-item `ancestor.specific` calls in templates (which issue one
    query per ancestor) with a single batched fetch via Wagtail's
    PageQuerySet.specific().
    """
    if not queryset:
        return queryset
    return queryset.specific()


@register.filter
def visible_breadcrumb_ancestors(ancestors):
    """Return only the ancestors that appear as visible breadcrumb items.

    Filters out root pages and pages excluded by exclude_from_breadcrumbs,
    returning a plain list safe to iterate multiple times (e.g. for both the
    HTML nav and the JSON-LD structured data block).
    """
    if not ancestors:
        return []
    return [a for a in ancestors if not a.is_root() and not exclude_from_breadcrumbs(a)]


@register.filter
def exclude_from_breadcrumbs(page):
    """
    Check if a page's model should be excluded from breadcrumbs.
    Returns True if the page should be excluded, False otherwise.
    """
    if not page or not hasattr(page, "_meta"):
        return False

    return page._meta.model_name.lower() in EXCLUDED_BREADCRUMB_MODELS
