import logging

from django.core.management.base import BaseCommand

from contact.models import ContactPublicationStatistics, Meeting, Organization, Person

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Generate or update publication statistics for all contacts"

    def add_arguments(self, parser):
        parser.add_argument(
            "--type",
            choices=["person", "meeting", "organization", "all"],
            default="all",
            help="Type of contacts to update statistics for",
        )

    def handle(self, *args, **options):
        contact_type = options["type"]
        updated_count = 0

        if contact_type in ["person", "all"]:
            self.stdout.write("Updating statistics for people...")
            for person in Person.objects.all():
                ContactPublicationStatistics.update_for_contact(person)
                updated_count += 1

        if contact_type in ["meeting", "all"]:
            self.stdout.write("Updating statistics for meetings...")
            for meeting in Meeting.objects.all():
                ContactPublicationStatistics.update_for_contact(meeting)
                updated_count += 1

        if contact_type in ["organization", "all"]:
            self.stdout.write("Updating statistics for organizations...")
            for org in Organization.objects.all():
                ContactPublicationStatistics.update_for_contact(org)
                updated_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully updated publication statistics for {updated_count} contacts",
            ),
        )
