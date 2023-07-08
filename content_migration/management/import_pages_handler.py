from tqdm import tqdm
from content_migration.management.shared import (
    parse_csv_file,
    parse_media_blocks,
    parse_media_string_to_list,
)
from wagtail.models import Page
from home.models import HomePage
from wf_pages.models import WfPage
from content_migration.management.shared import (
    create_permanent_redirect,
    parse_body_blocks,
)


def import_page_item(page_data: dict[str, str], home_page: HomePage) -> Page:
    """Create or update a page instance from page data."""

    page_exists = WfPage.objects.filter(
        drupal_node_id=page_data["drupal_node_id"],
    ).exists()

    page_body_blocks = parse_body_blocks(page_data["body"])

    if page_data["media"] != "":
        page_media_blocks = parse_media_blocks(
            parse_media_string_to_list(page_data["media"]),
        )
    else:
        page_media_blocks = None

    if page_media_blocks:
        page_body_blocks.extend(page_media_blocks)

    if page_exists:
        page = WfPage.objects.get(drupal_node_id=page_data["drupal_node_id"])
        page.title = page_data["title"]
        page.body = page_body_blocks

        page.save()
    else:
        page = home_page.add_child(
            instance=WfPage(
                title=page_data["title"],
                drupal_node_id=page_data["drupal_node_id"],
                body=page_body_blocks,
            ),
        )

    return page


def handle_import_pages(file_name: str) -> None:
    # Get references to relevant index pages
    home_page = HomePage.objects.get()

    pages = parse_csv_file(file_name)

    for page_data in tqdm(
        pages,
        total=len(pages),
        desc="Pages",
        unit="row",
    ):
        page = import_page_item(page_data, home_page)

        # create permanent redirect from old path to new page
        create_permanent_redirect(
            redirect_path=page_data["url_path"],
            redirect_entity=page,
        )
