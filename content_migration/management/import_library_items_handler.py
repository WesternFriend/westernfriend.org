import logging
from tqdm import tqdm  # type: ignore
from content_migration.management.errors import (
    CouldNotFindMatchingContactError,
    DuplicateContactError,
)

from facets.models import (
    Audience,
    Genre,
    Medium,
    TimePeriod,
)
from library.models import (
    LibraryIndexPage,
    LibraryItem,
    LibraryItemAuthor,
)

from content_migration.management.shared import (
    create_permanent_redirect,
    get_existing_magazine_author_from_db,
    parse_body_blocks,
    parse_csv_file,
    parse_media_blocks,
    parse_media_string_to_list,
)

logging.basicConfig(
    filename="import_library_items.log",
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)


def add_library_item_authors(
    library_item: LibraryItem,
    drupal_author_ids: str,
) -> None:
    drupal_author_ids_int = [
        int(author_id) for author_id in drupal_author_ids.split(", ")
    ]

    for drupal_author_id in drupal_author_ids_int:
        try:
            author = get_existing_magazine_author_from_db(
                drupal_author_id,
            )
        except CouldNotFindMatchingContactError:
            logger.error(
                f"Could not find magazine author by ID: { int(drupal_author_id) }",
            )
            continue
        except DuplicateContactError:
            logger.error(
                f"Found multiple magazine authors by ID: { int(drupal_author_id) }",
            )
            continue

        if author:
            library_item_author_exists = LibraryItemAuthor.objects.filter(
                library_item=library_item,
                author=author,
            ).exists()

            if not library_item_author_exists:
                item_author = LibraryItemAuthor(
                    library_item=library_item,
                    author=author,
                )

                library_item.authors.add(item_author)


def add_library_item_keywords(
    library_item: LibraryItem,
    keywords: str,
) -> None:
    for keyword in keywords.split(", "):
        library_item.tags.add(keyword)


def handle_import_library_items(file_name: str) -> None:
    # Get the only instance of Magazine Department Index Page
    library_item_index_page = LibraryIndexPage.objects.get()

    library_items = parse_csv_file(file_name)

    for import_library_item in tqdm(
        library_items,
        desc="Library items",
        unit="row",
    ):
        library_item_exists = LibraryItem.objects.filter(
            drupal_node_id=import_library_item["drupal_node_id"],
        ).exists()

        if library_item_exists:
            library_item = LibraryItem.objects.get(
                drupal_node_id=import_library_item["drupal_node_id"],
            )
        else:
            library_item = LibraryItem(
                title=import_library_item["title"],
                drupal_node_id=import_library_item["drupal_node_id"],
            )

            # Add library item to library branch of content tree
            library_item_index_page.add_child(instance=library_item)

            library_item_index_page.save()

        library_item.title = import_library_item["title"]
        library_item.body = parse_body_blocks(import_library_item["description"])

        library_item.body += parse_media_blocks(
            parse_media_string_to_list(import_library_item["media"]),
        )

        # Audience
        if import_library_item["audience"] != "":
            try:
                library_item.item_audience = Audience.objects.get(
                    title=import_library_item["audience"],
                )
            except Audience.DoesNotExist:
                logger.error(
                    f"Could not find audience by title: { import_library_item['audience'] }",  # noqa: E501
                )

        # Genre
        if import_library_item["genre"] != "":
            try:
                library_item.item_genre = Genre.objects.get(
                    title=import_library_item["genre"],
                )
            except Genre.DoesNotExist:
                logger.error(
                    f"Could not find genre by title: { import_library_item['genre'] }",
                )

        # Medium
        if import_library_item["medium"] != "":
            try:
                library_item.item_medium = Medium.objects.get(
                    title=import_library_item["medium"],
                )
            except Medium.DoesNotExist:
                logger.error(
                    f"Could not find medium by title: { import_library_item['medium'] }",  # noqa: E501
                )
        # Time Period
        if import_library_item["time_period"] != "":
            try:
                library_item.item_time_period = TimePeriod.objects.get(
                    title=import_library_item["time_period"],
                )
            except TimePeriod.DoesNotExist:
                logger.error(
                    f"Could not find time period by title: { import_library_item['time_period'] }",  # noqa: E501
                )

        # Authors
        if import_library_item["drupal_magazine_author_ids"] != "":
            add_library_item_authors(
                library_item,
                import_library_item["drupal_magazine_author_ids"],
            )

        # Keywords
        if import_library_item["keywords"] != "":
            add_library_item_keywords(
                library_item,
                import_library_item["keywords"],
            )

        # Website
        if import_library_item["website"] != "":
            url_stream_block = (
                "url",
                import_library_item["website"],
            )

            # TODO: Remember to remove this type ignore and make this line safer
            library_item.body.append(url_stream_block)  # type: ignore

        library_item.save()

        # create redirect to library item
        create_permanent_redirect(
            redirect_path=import_library_item["url_path"],
            redirect_entity=library_item,
        )
