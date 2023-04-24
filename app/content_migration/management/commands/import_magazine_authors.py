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


def create_meeting(author):
    meeting_index_page = MeetingIndexPage.objects.get()

    meeting_name = author["drupal_full_name"]
    drupal_author_id = author["drupal_author_id"]

    if author["civicrm_id"] == None:
        logger.error(f"Meeting {meeting_name} does not have CiviCRM ID")

    try:
        meeting = Meeting(
            title=meeting_name,
            drupal_author_id=drupal_author_id,
            civicrm_id=author["civicrm_id"],
        )
    except:
        logger.error(
            f"Could not create meeting for {meeting_name} (ID: {drupal_author_id})"
        )

        meeting_index_page.add_child(instance=meeting)

        meeting_index_page.save()


def create_organization(author):
    organization_index_page = OrganizationIndexPage.objects.get()

    organization_name = author["drupal_full_name"]
    drupal_author_id = author["drupal_author_id"]

    if author["civicrm_id"] == None:
        logger.error(f"Organization {organization_name} does not have CiviCRM ID")

    try:
        organization = Organization(
            title=organization_name,
            drupal_author_id=drupal_author_id,
            civicrm_id=author["civicrm_id"],
        )
    except:
        logger.error(
            f"Could not create organization {organization_name} (ID: {drupal_author_id})"
        )

        organization_index_page.add_child(instance=organization)

        organization_index_page.save()


def create_person(author):
    person_index_page = PersonIndexPage.objects.get()

    try:
        person = Person(
            given_name=author["given_name"],
            family_name=author["family_name"],
            drupal_author_id=author["drupal_author_id"],
            civicrm_id=author["civicrm_id"],
        )
    except:
        logger.error(f"Could not create person ID: { author['drupal_author_id'] }")

        person_index_page.add_child(instance=person)

        person_index_page.save()


def import_author_records(authors_list):
    for author in tqdm(authors_list, desc="Primary Author records", unit="row"):

        # Don't import duplicate authors
        # Instead, clean them up in the Drupal site
        if author["duplicate_of_id"] != None:
            logger.warning(
                f"Author { author['drupal_author_id'] } is marked as a duplicate"
            )

            # continue to next author record
            continue
        else:
            if author["author_type"] == "meeting":
                create_meeting(author)
            elif author["author_type"] == "organization":
                create_organization(author)
            elif author["author_type"] == "person":
                create_person(author)
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
            pd.read_excel(options["file"]).replace({np.nan: None}).to_dict("records")
        )

        import_author_records(authors_list)
