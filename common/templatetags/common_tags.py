from django import template

register = template.Library()


@register.filter
def model_name(value):
    """Return the model name of the given object."""

    if value and hasattr(value, "_meta"):
        return value._meta.model_name
    return ""


EXCLUDED_BREADCRUMB_MODELS = [
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
def exclude_from_breadcrumbs(page):
    """
    Check if a page's model should be excluded from breadcrumbs.
    Returns True if the page should be excluded, False otherwise.
    """
    if not page or not hasattr(page, "_meta"):
        return False

    return page._meta.model_name.lower() in EXCLUDED_BREADCRUMB_MODELS
