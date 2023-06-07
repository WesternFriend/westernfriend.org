from django.core.exceptions import ValidationError
from django.db import IntegrityError

from tqdm import tqdm

from wagtail.contrib.redirects.models import Redirect
from content_migration.management.shared import (
    parse_body_blocks,
    parse_csv_file,
    parse_media_blocks,
)

from documents.models import PublicBoardDocument, PublicBoardDocumentIndexPage


def get_board_document_category_key(category_label: str) -> str | None:
    category_value = None

    if category_label == "Corporation Documents - current year":
        category_value = "corporation_documents_current_year"
    elif category_label == "Corporation Documents - prior years":
        category_value = "corporation_documents_prior_years"
    elif category_label == "Annual Reports":
        category_value = "annual_reports"
    elif category_label == "Relations with Monthly Meetings":
        category_value = "relations_with_monthly_meetings"
    else:
        print("Unknown category label:", category_label)

    return category_value


def handle_import_board_documents(file_name: str) -> None:
    # Get references to relevant index pages
    public_board_documents_index = PublicBoardDocumentIndexPage.objects.get()

    # get a reference to the root site
    root_site = public_board_documents_index.get_site()

    board_docs_data = parse_csv_file(file_name)

    for document_data in tqdm(
        board_docs_data,
        total=len(board_docs_data),
        desc="Documents",
        unit="row",
    ):
        # Make sure no board document exists with matching drupal_node_id
        board_document_exists = PublicBoardDocument.objects.filter(
            drupal_node_id=document_data["drupal_node_id"]
        ).exists()

        if not board_document_exists:
            # Create a new board document
            board_document = PublicBoardDocument(
                title=document_data["title"],
                publication_date=document_data["publication_date"],
                drupal_node_id=document_data["drupal_node_id"],
            )

            # Convert the board document category TextChoice label
            # to a BoardDocumentCategory key
            board_document.category = get_board_document_category_key(
                document_data["board_document_category"]
            )

            # Parse the document's body, if it is not empty
            if document_data["body"] is not None:
                board_document.body = parse_body_blocks(document_data["body"])

            # Append media to the document's body
            if document_data["media"] is not None:
                # download media from URL, convert it to a list of blocks,
                # and append it to the document's body
                board_document.body += parse_media_blocks(
                    document_data["media"].split(", ")
                )

            # Add the document to the index page
            # catch a Validation Error if the category is null
            try:
                public_board_documents_index.add_child(instance=board_document)
            except ValidationError:
                print(
                    "Validation Error for: ",
                    document_data["title"],
                    " with category: ",
                    document_data["board_document_category"],
                )

                # Continue to the next document,
                # since we can't add a document to the index page without a category
                continue

            # # create a Wagtail redirect from the old url to the new one
            try:
                Redirect.objects.create(
                    old_path=document_data["url_path"],  # the old path from Drupal
                    site=root_site,  # the root site
                    redirect_page=board_document,  # the new page
                    is_permanent=True,  # permanent redirect
                ).save()
            except IntegrityError:
                print(
                    "Redirect already exists for: ",
                    document_data["url_path"],
                    " to ",
                    board_document,
                )
