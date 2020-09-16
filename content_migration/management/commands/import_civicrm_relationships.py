# Once contacts are imported, we will create relationships
# Since Meetings are hierarchical along with Wagtail Pages,
# we need to move the existing pages to the correct parent.
# https://stackoverflow.com/a/57057466/1191545

import csv
import re

from django.core.management.base import BaseCommand, CommandError
from django.core.exceptions import ObjectDoesNotExist

from wagtail.core.models import Page

from contact.models import Meeting


def extract_contact_id_from(contact_name):
    # Contact names contain contact ID in parenthesis
    regex = r"([0-9]+)"

    match = re.search(regex, contact_name).group(0)

    return int(match)


def extract_contact_ids_from(relationship):
    parent_name = relationship["Contact B"]
    child_name = relationship["Contact A"]

    # print(f"{ child_name } belongs to { parent_name }")

    parent_id = extract_contact_id_from(parent_name)
    child_id = extract_contact_id_from(child_name)

    return {"parent_id": parent_id, "child_id": child_id}


class Command(BaseCommand):
    help = "Import Community Directory from Drupal site"

    def add_arguments(self, parser):
        parser.add_argument("--file", action="store", type=str)

    def handle(self, *args, **options):
        with open(options["file"]) as import_file:
            relationships = csv.DictReader(import_file)

            for relationship in relationships:

                contact_ids = extract_contact_ids_from(relationship)

                try:
                    parent = Meeting.objects.get(civicrm_id=contact_ids["parent_id"])
                except ObjectDoesNotExist:
                    print(
                        f"Could not find contact with CiviCRM ID { contact_ids['parent_id'] }"
                    )
                    pass

                try:
                    child = Meeting.objects.get(civicrm_id=contact_ids["child_id"])
                except ObjectDoesNotExist:
                    print(
                        f"Could not find contact with CiviCRM ID { contact_ids['child_id'] }"
                    )
                    pass

                child.move(parent, pos="last-child")

                # page = child.specific_class.objects.get(id=child.id)

        self.stdout.write("All done!")
