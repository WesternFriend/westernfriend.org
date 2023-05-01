import logging

import numpy as np
import pandas as pd
from django.core.management.base import BaseCommand
from tqdm import tqdm

from contact.models import (
    Meeting,
    MeetingIndexPage,
    Organization,
    OrganizationIndexPage,
    Person,
    PersonIndexPage,
)

logging.basicConfig(
    filename="magazine_author_import.log",
    level=logging.ERROR,
    format="%(message)s",
    # format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)


def create_meeting(author, meeting_index_page):
    meeting = Meeting(
        title=author["drupal_full_name"],
        drupal_author_id=author["drupal_author_id"],
        civicrm_id=author["civicrm_contact_id"],
    )

    meeting_index_page.add_child(instance=meeting)

    meeting_index_page.save()


def create_organization(author, organization_index_page):
    organization = Organization(
        title=author["drupal_full_name"],
        drupal_author_id=author["drupal_author_id"],
        civicrm_id=author["civicrm_contact_id"],
    )

    organization_index_page.add_child(instance=organization)

    organization_index_page.save()


def create_person(author, person_index_page):
    person = Person(
        given_name=author["given_name"],
        family_name=author["family_name"],
        drupal_author_id=author["drupal_author_id"],
        civicrm_id=author["civicrm_contact_id"],
    )

    person_index_page.add_child(instance=person)

    person_index_page.save()


def import_author_records(authors_list):
    meeting_index_page = MeetingIndexPage.objects.get()
    organization_index_page = OrganizationIndexPage.objects.get()
    person_index_page = PersonIndexPage.objects.get()

    for author in tqdm(authors_list, desc="Primary Author records", unit="row"):
        author_type = author["author_type"]

        # Don't import duplicate authors
        # Instead, clean them up in the Drupal site
        if author["duplicate_of_id"] is not None:
            logger.warning(
                f"Author { author['drupal_author_id'] } is marked as a duplicate"
            )

            # continue to next author record
            continue
        else:
            if author_type == "meeting":
                create_meeting(author, meeting_index_page)
            elif author_type == "organization":
                create_organization(author, organization_index_page)
            elif author_type == "person":
                create_person(author, person_index_page)
            else:
                logger.error(
                    f"Unknown author type for ID: { author['drupal_author_id'] }"
                )


class Command(BaseCommand):
    help = "Import Authors from Drupal site"

    def add_arguments(self, parser):
        parser.add_argument("--file", action="store", type=str)

    def handle(self, *args, **options):
        authors_list = (
            pd.read_csv(options["file"]).replace({np.nan: None}).to_dict("records")
        )

        import_author_records(authors_list)
