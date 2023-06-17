from datetime import datetime
from tqdm import tqdm
from community.models import OnlineWorship, OnlineWorshipIndexPage
from content_migration.management.errors import (
    CouldNotFindMatchingContactError,
    CouldNotParseAuthorIdError,
)
from content_migration.management.shared import (
    construct_import_file_path,
    create_permanent_redirect,
    get_existing_magazine_author_from_db,
    parse_csv_file,
)


TIMEZONE_CONVERSIONS = {
    "Pacific": "US/Pacific",
    "Mountain": "US/Mountain",
    "Central": "US/Central",
    "Eastern": "US/Eastern",
}


def get_time_or_none(time_str: str) -> str | None:
    """Take a time in 24 hour integer format and return a time ztring in HH:MM
    format."""
    if time_str == "":
        return None

    try:
        time_obj = datetime.strptime(time_str, "%H%M").time()
    except ValueError as error:
        raise ValueError(f"Unexpected time: {time_str}") from error

    return time_obj.strftime("%H:%M")


def get_timezone_or_none(timezone: str) -> str | None:
    """Ensure that the timezone is in the proper format."""
    if timezone == "":
        return None

    try:
        return TIMEZONE_CONVERSIONS[timezone]
    except KeyError as error:
        raise ValueError(f"Unexpected timezone: {timezone}") from error


def handle_import_online_worship_item(
    item: dict,
    index_page: OnlineWorshipIndexPage,
) -> OnlineWorship:
    """Import a single online worship item from Drupal."""

    # check if news item exists
    online_worship_exists = OnlineWorship.objects.filter(
        drupal_node_id=item["drupal_node_id"]
    ).exists()

    title = item["title"]
    description = item["body"]
    hosted_by = get_existing_magazine_author_from_db(
        drupal_author_id=item["magazine_author_id"]
    )
    # times_of_worship = item["times_of_worship"]
    website = item["online_worship_url"]
    drupal_node_id = item["drupal_node_id"]
    drupal_body_migrated = item["body"]
    drupal_url_path = item["url_path"]
    online_worship_day = item["online_worship_day"]
    online_worship_time = get_time_or_none(item["online_worship_time"])
    online_worship_timezone = get_timezone_or_none(item["online_worship_timezone"])

    if online_worship_exists:
        online_worship_db = OnlineWorship.objects.get(
            drupal_node_id=item["drupal_node_id"]
        )
        online_worship_db.title = title
        online_worship_db.description = description
        online_worship_db.hosted_by = hosted_by
        # online_worship_db.times_of_worship = item["times_of_worship"]
        online_worship_db.website = website
        online_worship_db.drupal_body_migrated = drupal_body_migrated
        online_worship_db.drupal_url_path = drupal_url_path
        online_worship_db.online_worship_day = online_worship_day
        online_worship_db.online_worship_time = online_worship_time
        online_worship_db.online_worship_timezone = online_worship_timezone

        online_worship_db.save()
    else:
        online_worship_db = OnlineWorship(
            title=title,
            description=description,
            hosted_by=hosted_by,
            # times_of_worship=times_of_worship,
            website=website,
            drupal_node_id=drupal_node_id,
            drupal_body_migrated=drupal_body_migrated,
            drupal_url_path=drupal_url_path,
            online_worship_day=online_worship_day,
            online_worship_time=online_worship_time,
            online_worship_timezone=online_worship_timezone,
        )

        index_page.add_child(instance=online_worship_db)

    return online_worship_db


def handle_import_online_worship() -> None:
    """Import news from Drupal."""
    online_worship_items_data = parse_csv_file(
        construct_import_file_path(file_key="online_worship"),
    )
    index_page = OnlineWorshipIndexPage.objects.get()

    for online_worship_item_data in tqdm(
        online_worship_items_data,
        desc="Online worship items",
    ):
        try:
            online_worship_db: OnlineWorship = handle_import_online_worship_item(
                item=online_worship_item_data,
                index_page=index_page,
            )
        except CouldNotFindMatchingContactError:
            continue
        except CouldNotParseAuthorIdError:
            continue

        create_permanent_redirect(
            redirect_path=online_worship_item_data["url_path"],
            redirect_entity=online_worship_db,
        )
