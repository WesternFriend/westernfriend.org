# Once contacts are imported, we will create relationships
# Since Meetings are hierarchical along with Wagtail Pages,
# we need to move the existing pages to the correct parent.
# https://stackoverflow.com/a/57057466/1191545

import csv
import re

from django.core.management.base import BaseCommand, CommandError
from django.core.exceptions import ObjectDoesNotExist

from contact.models import Meeting, MeetingPresidingClerk, Person, PersonIndexPage


def extract_contact_id_from(contact_name):
    # Contact names contain contact ID in parenthesis
    regex = r"([0-9]+)"

    match = re.search(regex, contact_name).group(0)

    return int(match)


def extract_given_name(given_name_with_contact_id):
    # name is first part before empty space
    return given_name_with_contact_id.split(" ")[0]


def extract_given_and_family_name(contact_name):
    """
    Extract given and family names from a CiviCRM contact name string.

    CiviCRM contact export contains name in the following format.

    "family_name, given_name (contact_id)"
    """

    try:
        family_name, given_name_with_contact_id = contact_name.split(", ")
    except ValueError:
        family_name = ""
        given_name_with_contact_id = contact_name

    given_name = extract_given_name(given_name_with_contact_id)

    return [family_name, given_name]


def extract_contact_ids_from(relationship):
    meeting_name = relationship["Contact B"]
    clerk_name = relationship["Contact A"]

    meeting_id = extract_contact_id_from(meeting_name)
    clerk_id = extract_contact_id_from(clerk_name)

    return {"meeting_id": meeting_id, "clerk_id": clerk_id}


class Command(BaseCommand):
    help = "Import Community Directory from Drupal site"

    def add_arguments(self, parser):
        parser.add_argument("--file", action="store", type=str)

    def handle(self, *args, **options):
        with open(options["file"]) as import_file:
            relationships = csv.DictReader(import_file)

            for relationship in relationships:

                contact_ids = extract_contact_ids_from(relationship)

                meeting_exists = Meeting.objects.filter(
                    civicrm_id=contact_ids["meeting_id"],
                ).exists()

                try:
                    meeting = Meeting.objects.get(civicrm_id=contact_ids["meeting_id"])
                except ObjectDoesNotExist:
                    print(
                        f"Could not find meeting with CiviCRM ID { contact_ids['meeting_id'] }"
                    )
                    pass

                # try:
                #     clerk = Person.objects.get(civicrm_id=contact_ids["clerk_id"])
                # except ObjectDoesNotExist:
                #     print(
                #         f"Could not find person with CiviCRM ID { contact_ids['clerk_id'] }"
                #     )
                #     pass

                family_name, given_name = extract_given_and_family_name(relationship["Contact A"])

                person_exists = Person.objects.filter(
                    given_name=given_name,
                    family_name=family_name,
                ).exists()

                if person_exists:
                    person = Person.objects.get(
                        given_name=given_name,
                        family_name=family_name,
                    )
                else:
                    person = Person(
                        given_name=given_name,
                        family_name=family_name,
                    )

                    # Get the only instance of Person Index Page
                    person_index_page = PersonIndexPage.objects.get()

                    # Add person to site page hiererchy
                    person_index_page.add_child(instance=person)
                    person_index_page.save()

                print(meeting)
                print(person)

                meeting_presiding_clerk = MeetingPresidingClerk(
                    meeting=meeting,
                    person=person,
                )

                meeting_presiding_clerk.save()

        self.stdout.write("All done!")
