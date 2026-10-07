import json

from django import template
from django.core.serializers.json import DjangoJSONEncoder
from django.template.defaultfilters import striptags
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
    return mark_safe(json_str.translate(_JSON_SCRIPT_ESCAPES))  # noqa: S308 - <, >, & are escaped above


@register.simple_tag
def magazine_article_json_ld(page):
    """Build schema.org data for a magazine article."""
    issue = page.get_parent().specific
    authors = []
    for article_author in page.authors.all():
        author_page = article_author.author
        author = {
            "@type": (
                "Person"
                if author_page.specific_class_name == "Person"
                else "Organization"
            ),
            "name": author_page.title,
        }
        if author["@type"] == "Person":
            person = author_page.specific
            author["givenName"] = person.given_name
            author["familyName"] = person.family_name
        authors.append(author)

    result = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": page.title,
        "author": authors,
        "datePublished": issue.publication_date,
        "publisher": {"@type": "Organization", "name": "Western Friend"},
        "isAccessibleForFree": page.is_public_access,
        "articleSection": page.department.title,
        "isPartOf": {
            "@type": "PublicationIssue",
            "issueNumber": issue.issue_number,
            "datePublished": issue.publication_date,
            "name": issue.title,
        },
        "mainEntityOfPage": {"@type": "WebPage", "@id": page.full_url},
    }
    if page.teaser:
        result["description"] = striptags(page.teaser)
    if page.tags.exists():
        result["keywords"] = [str(tag) for tag in page.tags.all()]
    return result


@register.simple_tag
def memorial_json_ld(page):
    """Build schema.org data for a memorial."""
    person = page.memorial_person
    about = {
        "@type": "Person",
        "name": person.title,
        "givenName": person.given_name,
        "familyName": person.family_name,
    }
    if page.date_of_birth:
        about["birthDate"] = page.date_of_birth
    if page.date_of_death:
        about["deathDate"] = page.date_of_death

    result = {
        "@context": "https://schema.org",
        "@type": "Article",
        "articleSection": "Memorial",
        "headline": page.title,
        "about": about,
        "mainEntityOfPage": {"@type": "WebPage", "@id": page.full_url},
    }
    if page.memorial_meeting:
        result["publisher"] = {
            "@type": "Organization",
            "name": page.memorial_meeting.title,
        }
    return result


@register.simple_tag(takes_context=True)
def breadcrumb_json_ld(context, page, visible_ancestors):
    """Build schema.org breadcrumb data from the pages shown in the breadcrumb."""
    request = context.get("request")
    items = [
        {
            "@type": "ListItem",
            "position": 1,
            "name": "Home",
            "item": _site_root(request) + "/" if request else "",
        }
    ]
    for position, ancestor in enumerate(visible_ancestors, start=2):
        items.append(
            {
                "@type": "ListItem",
                "position": position,
                "name": ancestor.title,
                "item": ancestor.get_full_url(request) if request else ancestor.url,
            }
        )
    items.append(
        {
            "@type": "ListItem",
            "position": len(visible_ancestors) + 2,
            "name": page.title,
            "item": page.get_full_url(request) if request else page.url,
        }
    )
    return {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": items,
    }


@register.simple_tag(takes_context=True)
def absolute_static(context, path):
    """Return a fully qualified URL for a static file.

    Structured data needs absolute URLs, and STATIC_URL is relative
    unless static files are served from a CDN such as Spaces.
    """
    url = static(path)
    request = context.get("request")
    return request.build_absolute_uri(url) if request else url


def _site_root(request) -> str:
    """Return the current Wagtail site's root URL, without a trailing slash.

    Using the site's configured hostname means www and bare-domain requests
    produce the same absolute URLs.
    """
    site = Site.find_for_request(request)
    return site.root_url if site else request.build_absolute_uri("/").rstrip("/")


@register.simple_tag(takes_context=True)
def site_root_url(context):
    """Return the absolute URL of the current Wagtail site's home page."""
    request = context.get("request")
    return f"{_site_root(request)}/" if request else ""


@register.simple_tag(takes_context=True)
def canonical_url(context):
    """Return the absolute canonical URL for the current page or request."""
    request = context.get("request")
    page = context.get("page")
    if page is not None and hasattr(page, "get_full_url"):
        url = page.get_full_url(request)
        if url:
            return url
    return f"{_site_root(request)}{request.path}" if request else ""


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
