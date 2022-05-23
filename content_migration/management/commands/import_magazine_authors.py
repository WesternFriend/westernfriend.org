import csv
from django.core.management.base import BaseCommand, CommandError

from tqdm import tqdm

from contact.models import (
    Meeting,
    MeetingIndexPage,
    Organization,
    OrganizationIndexPage,
    Person,
    PersonIndexPage,
)


def create_meeting(author):
    meeting_index_page = MeetingIndexPage.objects.get()

    meeting_name = author["meeting_name"]
    drupal_author_id = author["drupal_author_id"]

    meeting_exists = Meeting.objects.filter(
        drupal_author_id=drupal_author_id,
    ).exists()

    # Don't create duplicate meetings
    if not meeting_exists:
        try:
            meeting = Meeting(
                title=meeting_name,
                drupal_author_id=drupal_author_id,
            )
        except:
            print("Could not create meeting:", drupal_author_id)

        meeting_index_page.add_child(instance=meeting)

        meeting_index_page.save()


def create_organization(author):
    organization_index_page = OrganizationIndexPage.objects.get()

    organization_name = author["organization_name"]
    drupal_author_id = author["drupal_author_id"]

    organization_exists = Organization.objects.filter(
        drupal_author_id=drupal_author_id,
    ).exists()

    # Avoid duplicates
    if not organization_exists:
        try:
            organization = Organization(
                title=organization_name,
                drupal_author_id=drupal_author_id,
            )
        except:
            print("Could not create organization:", drupal_author_id)

        organization_index_page.add_child(instance=organization)

        organization_index_page.save()


def create_person(author):
    person_index_page = PersonIndexPage.objects.get()

    drupal_author_id = author["drupal_author_id"]

    person_exists = Person.objects.filter(
        drupal_author_id=drupal_author_id,
    ).exists()

    # Avoid duplicates
    if not person_exists:
        try:
            person = Person(
                given_name=author["given_name"],
                family_name=author["family_name"],
                drupal_author_id=drupal_author_id,
            )
        except:
            print("Could not create person: ", drupal_author_id)

        person_index_page.add_child(instance=person)

        person_index_page.save()


class Command(BaseCommand):
    help = "Import Authors from Drupal site"

    def add_arguments(self, parser):
        parser.add_argument("--file", action="store", type=str)

    def handle(self, *args, **options):
        with open(options["file"]) as import_file:
            authors = csv.DictReader(import_file)
            authors_list = list(authors)

            for author in tqdm(authors_list, desc="Authors", unit="row"):
                # Check for entity type among:
                # - Meeting
                # - Organization
                # - Person
                # with the condition to check for corrections to person names

                drupal_author_id = author["drupal_author_id"]

                author_is_meeting = author["meeting_name"] != ""
                author_is_organization = author["organization_name"] != ""
                author_is_person = (
                    author_is_meeting is False and author_is_organization is False
                )

                author_is_duplicate = author["duplicate of ID"] != ""

                if author_is_duplicate:
                    # don't create duplicate authors
                    pass
                else:
                    if author_is_meeting:
                        create_meeting(author)
                    elif author_is_organization:
                        create_organization(author)
                    elif author_is_person:
                        create_person(author)
                    else:
                        print("Unknown:", drupal_author_id)

        self.stdout.write("All done!")
