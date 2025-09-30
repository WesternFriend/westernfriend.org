from django.core.management.base import BaseCommand
from contact.factories import (
    MeetingFactory,
    OrganizationFactory,
    PersonFactory,
)
from contact.models import (
    MeetingIndexPage,
    OrganizationIndexPage,
    PersonIndexPage,
)


class Command(BaseCommand):
    help = "Generate random contacts"

    def handle(self, *args: tuple, **options: dict) -> None:
        self.stdout.write("Creating random contacts...")

        number_of_people = 30
        number_of_meetings = 30
        number_of_organizations = 10

        person_index_page = PersonIndexPage.objects.first()
        meeting_index_page = MeetingIndexPage.objects.first()
        organization_index_page = OrganizationIndexPage.objects.first()

        for _ in range(number_of_people):
            person = PersonFactory.build()
            person_index_page.add_child(instance=person)

        for _ in range(number_of_meetings):
            meeting = MeetingFactory.build()
            meeting_index_page.add_child(instance=meeting)

        for _ in range(number_of_organizations):
            organization = OrganizationFactory.build()
            organization_index_page.add_child(instance=organization)

        self.stdout.write(self.style.SUCCESS("Successfully created contacts"))
