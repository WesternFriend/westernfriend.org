from django.core.management.base import BaseCommand, CommandError

from wagtail.core.models import Page

from contact.models import (
    MeetingIndexPage,
    OrganizationIndexPage,
    PersonIndexPage
)
from home.models import HomePage
from community.models import CommunityPage


class Command(BaseCommand):
    help = "Create initial site structure"

    def handle(self, *args, **options):
        root_page = Page.objects.get(id=1)
        home_page = HomePage(
            title="Welcome"
        )
        community_page = CommunityPage(
            title="Community"
        )
        meeting_index_page = MeetingIndexPage(
            title="Meetings"
        )
        organization_index_page = OrganizationIndexPage(
            title="Organizations"
        )
        person_index_page = PersonIndexPage(
            title="People"
        )
        root_page.add_child(instance=home_page)
        root_page.save()

        home_page.add_child(instance=community_page)
        home_page.save()

        community_page.add_child(instance=meeting_index_page)
        community_page.add_child(instance=organization_index_page)
        community_page.add_child(instance=person_index_page)
        community_page.save()

        self.stdout.write("All done!")
