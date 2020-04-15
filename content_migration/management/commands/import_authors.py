import csv
from django.core.management.base import BaseCommand, CommandError

from contact.models import Meeting, Organization, Person


class Command(BaseCommand):
    help = "Import Authors from Drupal site"

    def add_arguments(self, parser):
        parser.add_argument("--file", action="store", type=str)

    def handle(self, *args, **options):
        with open(options["file"]) as import_file:
            authors = csv.DictReader(import_file)

            for author in authors:
                # Check for entity type among:
                # - Meeting
                # - Organization
                # - Person
                # with the condition to check for corrections to person names
                author_is_meeting = author["meeting_name"] is not ""
                author_is_organization = author["organization_name"] is not ""
                author_is_person = (
                    author["corrected_family_name"] is not "" or
                    author["corrected_given_name"] is not "" or
                    author["family_name"] is not "" or
                    author["given_name"] is not ""
                )

                if author_is_meeting:
                    print("meeting")
                elif author_is_organization:
                    print("organization")
                elif author_is_person:
                    print("person")
                else:
                    print("unknown")

                # # Get the only instance of Magazine Department Index Page
                # magazine_department_index_page = MagazineDepartmentIndexPage.objects.get()

                # import_department = MagazineDepartment(
                #     title=department["title"],
                # )

                # # Add department to site page hiererchy
                # magazine_department_index_page.add_child(instance=import_department)
                # magazine_department_index_page.save()

        self.stdout.write("All done!")
