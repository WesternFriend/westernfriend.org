# Once contacts are imported, we will create relationships
# Since Meetings are hierarchical along with Wagtail Pages,
# we need to move the existing pages to the correct parent.
# https://stackoverflow.com/a/57057466/1191545

import re

from django.core.exceptions import ObjectDoesNotExist
from tqdm import tqdm

from contact.models import Meeting
from content_migration.management.shared import parse_csv_file


def extract_contact_id_from(contact_name: str) -> int:
    # Contact names contain contact ID in parenthesis
    regex = r"([0-9]+)"

    # TODO: Handle case where contact name does not contain ID
    match = re.search(regex, contact_name).group(0)  # type: ignore

    return int(match)


def extract_contact_ids_from(relationship: dict) -> dict[str, int]:
    parent_name = relationship["Contact B"]
    child_name = relationship["Contact A"]

    parent_id = extract_contact_id_from(parent_name)
    child_id = extract_contact_id_from(child_name)

    return {"parent_id": parent_id, "child_id": child_id}


def handle_import_civicrm_relationships(file_name: str) -> None:
    relationships = parse_csv_file(file_name)

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
