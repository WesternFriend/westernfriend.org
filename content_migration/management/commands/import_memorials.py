import csv
from datetime import datetime

from django.core.management.base import BaseCommand, CommandError

from tqdm import tqdm


from memorials.models import Memorial, MemorialIndexPage
from contact.models import Meeting, Person, PersonIndexPage


def create_person(memorial_data):
    person = None

    person_index_page = PersonIndexPage.objects.get()

    try:
        person = Person(
            given_name=memorial_data["First Name"],
            family_name=memorial_data["Last Name"],
        )
    except:
        print("Could not create person: ", memorial_data["Article Author ID"])

    person_index_page.add_child(instance=person)

    person_index_page.save()

    return person


def get_memorial_meeting_or_none(memorial_data):
    meeting = None

    if memorial_data["Memorial Meeting"] != "":
        try:
            meeting = Meeting.objects.get(
                title=memorial_data["Memorial Meeting"]
            )
        except:
            print("Could not find memorial meeting:", memorial_data['Memorial Meeting'])

            return None

    return meeting


def get_or_create_memorial_person(memorial_data):
    person = None

    if memorial_data["Article Author ID"] != "n/a":
        try:
            person = Person.objects.get(
                drupal_author_id=int(memorial_data["Article Author ID"])
            )
        except:
            print("Could not find existing contact for Drupal ID:", memorial_data["Article Author ID"])
    else:
        person = create_person(memorial_data)

    return person


class Command(BaseCommand):
    help = "Import all memorial minutes"

    def add_arguments(self, parser):
        parser.add_argument("--file", action="store", type=str)

    def handle(self, *args, **options):
        # Get the only instance of Magazine Department Index Page
        memorial_index_page = MemorialIndexPage.objects.get()

        with open(options["file"]) as import_file:
            memorials = list(
                csv.DictReader(import_file)
            )

            for memorial_data in tqdm(
                memorials, desc="Memorials", unit="row"
            ):
                memorial_exists = Memorial.objects.filter(
                    drupal_memorial_id=int(memorial_data["memorial_id"])
                ).exists()

                if memorial_exists:
                    memorial = Memorial.objects.get(
                        drupal_memorial_id=int(memorial_data["memorial_id"])
                    )
                else:
                    memorial = Memorial(
                        title=f"{ memorial_data['First Name'] } { memorial_data['Last Name'] }",
                        drupal_memorial_id=int(memorial_data["memorial_id"]),
                    )

                memorial_person = get_or_create_memorial_person(memorial_data)

                if memorial_person is not None:
                    memorial.memorial_person = memorial_person
                else:
                    continue

                memorial.title = memorial_data["First Name"] + " " + memorial_data["Last Name"]
                memorial.memorial_minute = memorial_data["body"]

                # Strip out time from datetime strings
                datetime_format = "%Y-%m-%dT%X"

                # Dates are optional
                if memorial_data["Date of Birth"] != "":
                    memorial.date_of_birth = datetime.strptime(memorial_data["Date of Birth"], datetime_format)

                if memorial_data["Date of Death"] != "":
                    memorial.date_of_death = datetime.strptime(memorial_data["Date of Death"], datetime_format)

                if memorial_data["Dates are approximate"] != "":
                    memorial.dates_are_approximate = True

                memorial.memorial_meeting = get_memorial_meeting_or_none(memorial_data)

                if not memorial_exists:
                    # Add memorial to memorials collection
                    try:
                        memorial_index_page.add_child(instance=memorial)
                    except AttributeError:
                        print("Could not add memorial as child of memorial index page")

                    memorial_index_page.save()
                else:
                    memorial.save()
