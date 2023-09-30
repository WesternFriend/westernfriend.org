import typing


if typing.TYPE_CHECKING:
    from library.models import LibraryItem


QUERYSTRING_FACETS = [
    "item_audience__title",
    "item_genre__title",
    "item_medium__title",
    "item_time_period__title",
    "topics__topic__title",
    "authors__author__title",
    "title__icontains",
]


def filter_querystring_facets(
    query: dict,
) -> dict:
    """Filter querystring facets to only include those that are valid."""
    # remove empty items from query dict
    query = {k: v for k, v in query.items() if v}

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


def add_library_item_topics(
    library_item: "LibraryItem",
    topics: str,
) -> None:
    """Add topics to a library item."""
    
    # avoid circular import
    from facets.models import Topic
    from library.models import LibraryItemTopic

    topics = topics.split(";")

    for topic_title in topics:
        if topic_title == "":
            continue
        
        try:
            topic = Topic.objects.get(
                title=topic_title,
            )
        except Topic.DoesNotExist:
            print(f"Topic '{topic_title}' does not exist")
        
        library_item_topic = LibraryItemTopic(
            library_item=library_item,
            topic=topic,
        )
        
        library_item_topic.save()
