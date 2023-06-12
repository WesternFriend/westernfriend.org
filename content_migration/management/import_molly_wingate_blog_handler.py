"""Parse and import the Molly Wingate blog."""
from tqdm import tqdm
from content_migration.management.shared import (
    create_permanent_redirect,
    parse_body_blocks,
    parse_csv_file,
)
from content_migration.management.constants import (
    IMPORT_FILENAMES,
    LOCAL_MIGRATION_DATA_DIRECTORY,
)

from wf_pages.models import MollyWingateBlogIndexPage, MollyWingateBlogPage


def handle_import_molly_wingate_blog() -> None:
    """Parse and import the Molly Wingate blog."""
    # Get references to relevant index pages
    molly_wingate_blog_index_page = MollyWingateBlogIndexPage.objects.get()

    file_name = LOCAL_MIGRATION_DATA_DIRECTORY + IMPORT_FILENAMES["molly_wingate_blog"]

    pages = parse_csv_file(file_name)

    for page in tqdm(
        pages,
        total=len(pages),
        desc="Molly Wingate Blog",
        unit="row",
    ):
        molly_wingate_blog_page = MollyWingateBlogPage(
            title=page["title"],
            drupal_node_id=page["drupal_node_id"],
            body=parse_body_blocks(page["body"]),
            body_migrated=page["body"],
            publication_date=page["publication_date"],
        )

        molly_wingate_blog_index_page.add_child(instance=molly_wingate_blog_page)

        create_permanent_redirect(
            redirect_path=page["drupal_path"],
            redirect_entity=molly_wingate_blog_page,
        )

    molly_wingate_blog_index_page.save()
