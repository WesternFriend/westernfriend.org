from django.core.exceptions import ValidationError
from django.db import IntegrityError

import numpy as np
import pandas as pd
from tqdm import tqdm  # type: ignore

from wagtail.contrib.redirects.models import Redirect
from contact.models import Meeting
from content_migration.management.shared import (
    parse_body_blocks,
    parse_media_blocks,
)

from documents.models import MeetingDocument, MeetingDocumentIndexPage


def get_meeting_document_type_key(category_label: str) -> str | None:
    category_value = None

    if category_label == "Epistle":
        category_value = "epistle"
    elif category_label == "Minute of Concern":
        category_value = "minute"
    elif category_label == "Photos":
        category_value = "photos"
    else:
        print("Unknown category label:", category_label)

    return category_value


def handle_import_meeting_documents(file_name: str) -> None:
    # Get references to relevant index pages
    meeting_documents_index = MeetingDocumentIndexPage.objects.get()

    # get a reference to the root site
    root_site = meeting_documents_index.get_site()

    meeting_docs_data = (
        pd.read_csv(file_name).replace({np.nan: None}).to_dict("records")
    )

    for document_data in tqdm(
        meeting_docs_data,
        total=len(meeting_docs_data),
        desc="Documents",
        unit="row",
    ):
        # Make sure no meeting document exists with matching drupal_node_id
        meeting_document_exists = MeetingDocument.objects.filter(
            drupal_node_id=document_data["drupal_node_id"]
        ).exists()

        try:
            publishing_meeting = Meeting.objects.get(
                drupal_author_id=document_data["publishing_meeting_drupal_id"]
            )
        except Meeting.DoesNotExist:
            print(
                "Can't find publishing meeting for document: ",
                document_data["drupal_node_id"],
            )
            continue

        if not meeting_document_exists:
            # Create a new meeting document
            meeting_document = MeetingDocument(
                title=document_data["title"],
                publication_date=document_data["publication_date"],
                drupal_node_id=document_data["drupal_node_id"],
            )

            # Link the meeting document to the publishing meeting
            meeting_document.publishing_meeting = publishing_meeting

            # Convert the meeting document category TextChoice label
            # to a MeetingDocumentType key
            meeting_document.document_type = get_meeting_document_type_key(
                document_data["meeting_document_type"]
            )

            # Parse the document's body, if it is not empty
            if document_data["body"] is not None:
                meeting_document.body = parse_body_blocks(document_data["body"])

            # Append media to the document's body
            if document_data["media"] is not None:
                # download media from URL, convert it to a list of blocks,
                # and append it to the document's body
                meeting_document.body += parse_media_blocks(document_data["media"])

            # Add the document to the index page
            # catch a Validation Error if the category is null
            try:
                meeting_documents_index.add_child(instance=meeting_document)
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

            # create a Wagtail redirect from the old url to the new one
            try:
                Redirect.objects.create(
                    old_path=document_data["url_path"],  # the old path from Drupal
                    site=root_site,  # the root site
                    redirect_page=meeting_document,  # the new page
                    is_permanent=True,  # permanent redirect
                ).save()
            except IntegrityError:
                print(
                    "Redirect already exists for: ",
                    document_data["url_path"],
                    " to ",
                    meeting_document,
                )
