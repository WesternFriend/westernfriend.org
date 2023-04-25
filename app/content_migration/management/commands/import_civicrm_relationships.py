# Once contacts are imported, we will create relationships
# Since Meetings are hierarchical along with Wagtail Pages,
# we need to move the existing pages to the correct parent.
# https://stackoverflow.com/a/57057466/1191545

import re

import pandas as pd
from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand
from tqdm import tqdm

from contact.models import Meeting


def extract_contact_id_from(contact_name):
    # Contact names contain contact ID in parenthesis
    regex = r"([0-9]+)"

    match = re.search(regex, contact_name).group(0)

    return int(match)


def extract_contact_ids_from(relationship):
    parent_name = relationship["Contact B"]
    child_name = relationship["Contact A"]

    parent_id = extract_contact_id_from(parent_name)
    child_id = extract_contact_id_from(child_name)

    return {"parent_id": parent_id, "child_id": child_id}


class Command(BaseCommand):
    help = "Import Community Directory from Drupal site"

    def add_arguments(self, parser):
        parser.add_argument("--file", action="store", type=str)

    def handle(self, *args, **options):
        relationships = pd.read_csv(options["file"]).to_dict("records")

        for relationship in tqdm(
            relationships,
            total=len(relationships),
            desc="Relationships",
            unit="row",
        ):

            contact_ids = extract_contact_ids_from(relationship)

            try:
                parent = Meeting.objects.get(civicrm_id=contact_ids["parent_id"])
            except ObjectDoesNotExist:
                print(
                    f"Could not find 'parent meeting' contact with CiviCRM ID { contact_ids['parent_id'] }"  # noqa: E501
                )
                print(relationship)

                pass
            try:
                child = Meeting.objects.get(civicrm_id=contact_ids["child_id"])
            except ObjectDoesNotExist:
                print(
                    f"Could not find 'child meeting' contact with CiviCRM ID { contact_ids['child_id'] }"  # noqa: E501
                )
                print(relationship)

                pass

            if parent and child:
                try:
                    child.move(parent, pos="last-child")
                except AttributeError:
                    print(f"Could not move { child } to { parent }.")

        self.stdout.write("All done!")
