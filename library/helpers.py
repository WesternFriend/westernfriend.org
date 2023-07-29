QUERYSTRING_FACETS = [
    "item_audience",
    "item_genre",
    "item_medium",
    "item_time_period",
    "topics",
    "authors",
]


def filter_querystring_facets(
    query: dict,
) -> dict:
    """Filter querystring facets to only include those that are valid."""
    facets = {}
    for key, value in query.items():
        if key in QUERYSTRING_FACETS:
            facets[key] = value
    return facets


def create_querystring_from_facets(
    facets: dict,
) -> str:
    """Create a querystring from facets."""

    # Join facets into a querystring
    # placing an ampersand between each key/value pair
    return "&".join(f"{key}={value}" for key, value in facets.items())
